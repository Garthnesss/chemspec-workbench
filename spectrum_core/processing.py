"""Append-only processing pipeline: raw → processed, with step history.

Ops produce new ``Spectrum`` copies; the caller's raw spectrum is never mutated.
Sessions store the step log so analysis can be replayed.

Pipeline ops
------------
- ``baseline`` — reuse ``baseline_correct`` (polynomial / optional asls/mpls)
- ``smooth`` — Savitzky–Golay via ``scipy.signal.savgol_filter``
- ``despike`` (optional) — replace outlier points with a local median when
  |y − rolling_median| > ``z_thresh`` × rolling MAD (or fixed ``threshold``).
  Simple teaching aid, not a research-grade spike remover.
- ``normalize`` (optional) — scale y by ``max`` (|y| peak) or ``area``
  (trapezoidal ∫|y| dx); documents scale in ``meta``.

Not compound identification — continuum / noise / scale prep only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

import numpy as np
from scipy.signal import savgol_filter

from spectrum_core.baseline import baseline_correct
from spectrum_core.errors import ProcessingError
from spectrum_core.spectrum import Spectrum

STEP_BASELINE = "baseline"
STEP_SMOOTH = "smooth"
STEP_DESPIKE = "despike"
STEP_NORMALIZE = "normalize"

PIPELINE_STEPS: tuple[str, ...] = (
    STEP_BASELINE,
    STEP_SMOOTH,
    STEP_DESPIKE,
    STEP_NORMALIZE,
)

NORMALIZE_MAX = "max"
NORMALIZE_AREA = "area"
NORMALIZE_MODES: tuple[str, ...] = (NORMALIZE_MAX, NORMALIZE_AREA)

SOFTWARE_NOTE_DEFAULT = "spectrum_core.processing"


def _utc_now_iso() -> str:
    """UTC timestamp with Z suffix (seconds resolution)."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _package_version() -> str:
    try:
        from spectrum_core import __version__ as _v

        return str(_v)
    except Exception:  # noqa: BLE001
        return ""


def _json_safe_params(params: Mapping[str, Any] | None) -> dict[str, Any]:
    """Coerce step params to JSON-friendly scalars / nested dicts."""
    if not params:
        return {}
    out: dict[str, Any] = {}
    for key, val in params.items():
        if val is None or isinstance(val, (bool, int, str)):
            out[str(key)] = val
        elif isinstance(val, float):
            if not np.isfinite(val):
                continue
            out[str(key)] = float(val)
        elif isinstance(val, (np.floating, np.integer)):
            f = float(val)
            if np.isfinite(f):
                out[str(key)] = int(val) if isinstance(val, np.integer) else f
        elif isinstance(val, dict):
            out[str(key)] = _json_safe_params(val)
        else:
            out[str(key)] = str(val)
    return out


@dataclass(frozen=True)
class ProcessingStep:
    """One immutable record in an append-only processing history."""

    name: str
    params: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    software_note: str = SOFTWARE_NOTE_DEFAULT

    def __post_init__(self) -> None:
        name = (self.name or "").strip().lower()
        if not name:
            raise ValueError("ProcessingStep.name must be non-empty")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "params", _json_safe_params(self.params))
        ts = self.timestamp or _utc_now_iso()
        object.__setattr__(self, "timestamp", ts)
        note = self.software_note or SOFTWARE_NOTE_DEFAULT
        object.__setattr__(self, "software_note", str(note))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "params": dict(self.params),
            "timestamp": self.timestamp,
            "software_note": self.software_note,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProcessingStep:
        if not isinstance(data, Mapping):
            raise ValueError("ProcessingStep must be an object")
        name = data.get("name")
        if not name:
            raise ValueError("ProcessingStep missing name")
        params = data.get("params") or {}
        if not isinstance(params, dict):
            raise ValueError("ProcessingStep.params must be an object")
        return cls(
            name=str(name),
            params=dict(params),
            timestamp=str(data.get("timestamp") or ""),
            software_note=str(data.get("software_note") or SOFTWARE_NOTE_DEFAULT),
        )


@dataclass
class ProcessingHistory:
    """Append-only list of ``ProcessingStep`` records."""

    steps: list[ProcessingStep] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.steps)

    def __iter__(self):
        return iter(self.steps)

    def copy(self) -> ProcessingHistory:
        return ProcessingHistory(steps=list(self.steps))

    def with_step(self, step: ProcessingStep) -> ProcessingHistory:
        """Return a new history with ``step`` appended (does not mutate self)."""
        return ProcessingHistory(steps=[*self.steps, step])

    def to_list(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.steps]

    @classmethod
    def from_list(cls, data: list[Any] | None) -> ProcessingHistory:
        if data is None:
            return cls()
        if not isinstance(data, list):
            raise ValueError("history must be a list of step objects")
        steps = [ProcessingStep.from_dict(item) for item in data]
        return cls(steps=steps)

    def summary_lines(self) -> list[str]:
        """Short human-readable lines for UI (name + key params)."""
        lines: list[str] = []
        for i, step in enumerate(self.steps, start=1):
            bits = [f"{k}={v}" for k, v in sorted(step.params.items())]
            param_s = ", ".join(bits) if bits else "(defaults)"
            lines.append(f"{i}. {step.name} ({param_s}) @ {step.timestamp}")
        return lines


@dataclass
class PipelineState:
    """Keep ``raw`` immutable and a separate ``working`` copy + history."""

    raw: Spectrum
    working: Spectrum
    history: ProcessingHistory = field(default_factory=ProcessingHistory)

    @classmethod
    def from_raw(cls, raw: Spectrum) -> PipelineState:
        return cls(raw=raw, working=raw.copy(), history=ProcessingHistory())

    def apply(self, step: ProcessingStep | str, params: Mapping[str, Any] | None = None) -> PipelineState:
        """Apply a step to ``working``; return new state (raw unchanged)."""
        new_working, new_history = apply_step(self.working, self.history, step, params)
        return PipelineState(raw=self.raw, working=new_working, history=new_history)

    def reset_to_raw(self) -> PipelineState:
        """Discard history; set working back to a copy of raw."""
        return PipelineState(
            raw=self.raw,
            working=self.raw.copy(),
            history=ProcessingHistory(),
        )


def make_step(
    name: str,
    params: Mapping[str, Any] | None = None,
    *,
    timestamp: str | None = None,
    software_note: str | None = None,
) -> ProcessingStep:
    """Build a ``ProcessingStep`` with defaults for timestamp / software note."""
    note = software_note
    if note is None:
        ver = _package_version()
        note = f"{SOFTWARE_NOTE_DEFAULT}" + (f" v{ver}" if ver else "")
    return ProcessingStep(
        name=name,
        params=dict(params or {}),
        timestamp=timestamp or "",
        software_note=note,
    )


# ---------------------------------------------------------------------------
# Ops
# ---------------------------------------------------------------------------


def op_baseline(
    spectrum: Spectrum,
    *,
    method: str = "polynomial",
    degree: int = 2,
    lam: float = 1e6,
    p: float = 0.01,
    half_window: int | None = None,
) -> Spectrum:
    """Baseline-correct via ``baseline_correct`` (new spectrum; raw untouched)."""
    try:
        deg = int(degree)
    except (TypeError, ValueError) as exc:
        raise ProcessingError(
            "baseline: degree must be an integer >= 0"
        ) from exc
    if deg < 0:
        raise ProcessingError(f"baseline: degree must be >= 0 (got {deg})")
    n = len(spectrum)
    if method == "polynomial" and n <= deg:
        raise ProcessingError(
            f"baseline (polynomial): need more than {deg} finite points "
            f"to fit degree-{deg}; spectrum length is {n}"
        )
    if half_window is not None:
        try:
            hw = int(half_window)
        except (TypeError, ValueError) as exc:
            raise ProcessingError(
                "baseline: half_window must be an integer or None"
            ) from exc
        if hw < 1:
            raise ProcessingError(
                f"baseline: half_window must be >= 1 when set (got {hw})"
            )
    try:
        return baseline_correct(
            spectrum,
            method=method,
            degree=deg,
            lam=lam,
            p=p,
            half_window=half_window,
        )
    except (ValueError, ImportError) as exc:
        # Re-wrap plain ValueError from baseline helpers as ProcessingError
        if isinstance(exc, ProcessingError):
            raise
        if isinstance(exc, ImportError):
            raise
        raise ProcessingError(f"baseline: {exc}") from exc


def op_smooth(
    spectrum: Spectrum,
    *,
    window_length: int = 11,
    polyorder: int = 3,
) -> Spectrum:
    """Savitzky–Golay smooth (``scipy.signal.savgol_filter``).

    ``window_length`` must be odd and >= ``polyorder + 1``. Points near the
    edges use SciPy's default mode (``interp``).
    """
    try:
        wl = int(window_length)
        po = int(polyorder)
    except (TypeError, ValueError) as exc:
        raise ProcessingError(
            "smooth (Savitzky–Golay): window_length and polyorder must be integers"
        ) from exc
    n = len(spectrum)
    if n < 3:
        raise ProcessingError(
            f"smooth (Savitzky–Golay): spectrum length ({n}) must be >= 3"
        )
    if wl < 3:
        raise ProcessingError(
            "smooth (Savitzky–Golay): window_length must be >= 3 "
            f"(got {wl})"
        )
    if wl % 2 == 0:
        raise ProcessingError(
            "smooth (Savitzky–Golay): window_length must be odd "
            f"(got {wl}); SciPy savgol_filter requires an odd window"
        )
    if po < 0:
        raise ProcessingError(
            f"smooth (Savitzky–Golay): polyorder must be >= 0 (got {po})"
        )
    if po >= wl:
        raise ProcessingError(
            "smooth (Savitzky–Golay): polyorder must be < window_length "
            f"(got polyorder={po}, window_length={wl})"
        )
    if wl > n:
        raise ProcessingError(
            "smooth (Savitzky–Golay): window_length "
            f"({wl}) cannot exceed spectrum length ({n})"
        )
    y = np.asarray(spectrum.y, dtype=float)
    smoothed = savgol_filter(y, window_length=wl, polyorder=po)
    out = spectrum.with_y(
        smoothed,
        title=(spectrum.title + " (smoothed)").strip(),
    )
    out.meta = {
        **spectrum.meta,
        "smooth_method": "savgol",
        "smooth_window_length": wl,
        "smooth_polyorder": po,
    }
    return out


def op_despike(
    spectrum: Spectrum,
    *,
    window: int = 5,
    z_thresh: float = 6.0,
) -> Spectrum:
    """Replace spike-like outliers with a local median.

    For each point, compute the median and MAD of a centered window of odd
    length ``window`` (excluding the point itself when possible). If
    ``|y − median| > z_thresh × MAD`` (MAD scaled by 1.4826 toward σ), replace
    ``y`` with that median. When MAD is ~0, a relative fallback
    ``|y − median| > z_thresh × max(|median|, ε)`` is used.

    This is a simple teaching / cleanup aid — not a research-grade despiker.
    """
    try:
        w = int(window)
        z = float(z_thresh)
    except (TypeError, ValueError) as exc:
        raise ProcessingError(
            "despike: window must be an integer and z_thresh a finite number"
        ) from exc
    n = len(spectrum)
    if w < 3 or w % 2 == 0:
        raise ProcessingError(
            "despike: window must be odd and >= 3 "
            f"(got {w}); need a symmetric neighborhood for the local median"
        )
    if not np.isfinite(z) or z <= 0:
        raise ProcessingError(
            f"despike: z_thresh must be a finite value > 0 (got {z_thresh!r})"
        )
    if w > n:
        raise ProcessingError(
            f"despike: window ({w}) cannot exceed spectrum length ({n})"
        )
    y = np.asarray(spectrum.y, dtype=float).copy()
    n = len(y)
    half = w // 2
    cleaned = y.copy()
    eps = 1e-12
    mad_scale = 1.4826
    n_replaced = 0
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        neigh = np.concatenate([y[lo:i], y[i + 1 : hi]]) if hi - lo > 1 else y[lo:hi]
        if neigh.size == 0:
            continue
        med = float(np.median(neigh))
        mad = float(np.median(np.abs(neigh - med)))
        delta = abs(float(y[i]) - med)
        if mad > eps:
            if delta > z * mad_scale * mad:
                cleaned[i] = med
                n_replaced += 1
        else:
            # Flat neighborhood: relative threshold
            if delta > z * max(abs(med), eps):
                cleaned[i] = med
                n_replaced += 1
    out = spectrum.with_y(
        cleaned,
        title=(spectrum.title + " (despiked)").strip(),
    )
    out.meta = {
        **spectrum.meta,
        "despike_window": w,
        "despike_z_thresh": z,
        "despike_replaced": n_replaced,
    }
    return out


def op_normalize(
    spectrum: Spectrum,
    *,
    mode: str = NORMALIZE_MAX,
) -> Spectrum:
    """Normalize y by peak ``max`` (|y|) or integrated ``area`` (trapz of |y|).

    Modes
    -----
    max :
        ``y / max(|y|)``. If the peak absolute value is ~0, returns a copy
        unchanged and sets ``meta['normalize_scale'] = 1.0``.
    area :
        ``y / ∫|y| dx`` (numpy trapezoid). If the area is ~0, same no-op
        behavior as max.

    Scale factor is stored in ``meta['normalize_scale']`` and mode in
    ``meta['normalize_mode']``. Does not change ``y_unit`` (still intensity /
    A / %T numerically scaled — document in UI that this is relative).
    """
    if not isinstance(mode, str) and mode is not None:
        raise ProcessingError(
            f"normalize: mode must be a string ({', '.join(NORMALIZE_MODES)}); "
            f"got {type(mode).__name__}"
        )
    key = (mode or NORMALIZE_MAX).strip().lower()
    if key not in NORMALIZE_MODES:
        raise ProcessingError(
            f"normalize: unknown mode {mode!r}; "
            f"known scientific modes: {', '.join(NORMALIZE_MODES)} "
            f"(max = scale by peak |y|; area = scale by ∫|y| dx)"
        )
    y = np.asarray(spectrum.y, dtype=float)
    x = np.asarray(spectrum.x, dtype=float)
    if len(spectrum) < 1:
        raise ProcessingError("normalize: spectrum must have at least one point")
    if key == NORMALIZE_MAX:
        peak = float(np.nanmax(np.abs(y))) if y.size else 0.0
        scale = peak if np.isfinite(peak) and peak > 0 else 1.0
    else:
        # area of |y| so sign of absorbance features is preserved relatively
        finite = np.isfinite(x) & np.isfinite(y)
        if int(np.count_nonzero(finite)) < 2:
            scale = 1.0
        else:
            area = float(np.trapezoid(np.abs(y[finite]), x[finite]))
            scale = area if np.isfinite(area) and abs(area) > 0 else 1.0
    out = spectrum.with_y(
        y / scale,
        title=(spectrum.title + f" (norm:{key})").strip(),
    )
    out.meta = {
        **spectrum.meta,
        "normalize_mode": key,
        "normalize_scale": scale,
    }
    return out


_OP_DISPATCH = {
    STEP_BASELINE: lambda spec, params: op_baseline(spec, **_baseline_kwargs(params)),
    STEP_SMOOTH: lambda spec, params: op_smooth(spec, **_smooth_kwargs(params)),
    STEP_DESPIKE: lambda spec, params: op_despike(spec, **_despike_kwargs(params)),
    STEP_NORMALIZE: lambda spec, params: op_normalize(spec, **_normalize_kwargs(params)),
}


def _baseline_kwargs(params: Mapping[str, Any]) -> dict[str, Any]:
    kw: dict[str, Any] = {}
    if "method" in params:
        kw["method"] = str(params["method"])
    if "degree" in params:
        kw["degree"] = int(params["degree"])
    if "lam" in params:
        kw["lam"] = float(params["lam"])
    if "p" in params:
        kw["p"] = float(params["p"])
    if "half_window" in params and params["half_window"] is not None:
        kw["half_window"] = int(params["half_window"])
    return kw


def _smooth_kwargs(params: Mapping[str, Any]) -> dict[str, Any]:
    kw: dict[str, Any] = {}
    if "window_length" in params:
        kw["window_length"] = int(params["window_length"])
    if "polyorder" in params:
        kw["polyorder"] = int(params["polyorder"])
    return kw


def _despike_kwargs(params: Mapping[str, Any]) -> dict[str, Any]:
    kw: dict[str, Any] = {}
    if "window" in params:
        kw["window"] = int(params["window"])
    if "z_thresh" in params:
        kw["z_thresh"] = float(params["z_thresh"])
    return kw


def _normalize_kwargs(params: Mapping[str, Any]) -> dict[str, Any]:
    kw: dict[str, Any] = {}
    if "mode" in params:
        kw["mode"] = str(params["mode"])
    return kw


def apply_step(
    spectrum: Spectrum,
    history: ProcessingHistory | None,
    step: ProcessingStep | str,
    params: Mapping[str, Any] | None = None,
) -> tuple[Spectrum, ProcessingHistory]:
    """Apply one pipeline step; return ``(new_spectrum, new_history)``.

    ``spectrum`` is treated as the current *working* copy — it is not mutated.
    ``history`` is treated as append-only: a new ``ProcessingHistory`` is
    returned with the step record added. Pass the caller's *raw* spectrum
    separately (see ``PipelineState``) so it stays untouched.

    Parameters
    ----------
    spectrum :
        Current working spectrum.
    history :
        Prior history (or ``None`` / empty).
    step :
        A ``ProcessingStep`` or a step name string (``baseline``, ``smooth``,
        ``despike``, ``normalize``). When a string is given, ``params`` is used.
    params :
        Step parameters when ``step`` is a name string (ignored if ``step`` is
        already a ``ProcessingStep``).
    """
    hist = history.copy() if history is not None else ProcessingHistory()
    if isinstance(step, ProcessingStep):
        record = step
    else:
        record = make_step(str(step), params)
    name = record.name
    if name not in _OP_DISPATCH:
        known = ", ".join(PIPELINE_STEPS)
        raise ProcessingError(
            f"unknown pipeline step {name!r}; known: {known}"
        )
    new_spec = _OP_DISPATCH[name](spectrum, record.params)
    # Ensure we never alias the input arrays
    if new_spec is spectrum:
        new_spec = spectrum.copy()
    new_hist = hist.with_step(record)
    return new_spec, new_hist


def replay_history(
    raw: Spectrum,
    history: ProcessingHistory | list[Any] | None,
) -> tuple[Spectrum, ProcessingHistory]:
    """Replay steps onto a copy of ``raw``; return working spectrum + history."""
    if isinstance(history, ProcessingHistory):
        hist = history
    else:
        hist = ProcessingHistory.from_list(history)
    working = raw.copy()
    built = ProcessingHistory()
    for step in hist.steps:
        working, built = apply_step(working, built, step)
    return working, built


__all__ = [
    "ProcessingError",
    "STEP_BASELINE",
    "STEP_SMOOTH",
    "STEP_DESPIKE",
    "STEP_NORMALIZE",
    "PIPELINE_STEPS",
    "NORMALIZE_MAX",
    "NORMALIZE_AREA",
    "NORMALIZE_MODES",
    "SOFTWARE_NOTE_DEFAULT",
    "ProcessingStep",
    "ProcessingHistory",
    "PipelineState",
    "make_step",
    "apply_step",
    "replay_history",
    "op_baseline",
    "op_smooth",
    "op_despike",
    "op_normalize",
]
