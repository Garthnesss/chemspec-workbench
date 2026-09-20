"""Versioned ChemSpec analysis session save / load (JSON).

Session files (``.csw.json`` / ``.chemspec.json``) embed the spectrum arrays so
reload works if the original path moves. They also store processing params,
optional append-only pipeline ``history`` steps, peaks (incl. FWHM/area),
optional notes, and a provenance snapshot. ``spectrum`` is the raw copy;
replay ``history`` for the working spectrum.

**Computational identity (format_version ≥ 2).** Sessions carry
``raw_data_hash`` (SHA-256 of a canonical **arrays-only** x‖y encoding —
**units are not** in this hash), optional ``source_path_hash``, and
``analysis_fingerprint`` (SHA-256 over identity fields including ``x_unit`` /
``y_unit``, normalized processing, history name/params, and peaks). Pipeline
step *timestamps* remain in ``history`` for provenance but **do not** enter
``analysis_fingerprint`` — re-running the same ops later yields the same
fingerprint. Callers comparing ``raw_data_hash`` alone must not assume unit
agreement; use ``analysis_fingerprint`` (or compare units explicitly).

v1 files load via ``migrate_session_dict`` → current version.

This is a reproducible *analysis* snapshot — not compound identification.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from spectrum_core.peaks import (
    AREA_DEF_TRAPZ_HALF_MAX,
    WIDTH_DEF_PROMINENCE_RELATIVE,
    Peak,
)
from spectrum_core.processing import ProcessingHistory
from spectrum_core.spectrum import Spectrum, XUnit, YUnit

SESSION_FORMAT_VERSION = 2
SESSION_FORMAT_VERSION_MIN = 1
SESSION_EXTENSIONS = (".csw.json", ".chemspec.json")

_X_UNITS = frozenset({"nm", "cm-1", "Hz", "MHz"})
_Y_UNITS = frozenset({"A", "percent_T", "intensity", "dB"})

DEFAULT_PROCESSING: dict[str, Any] = {
    "baseline_on": False,
    "baseline_method": "polynomial",
    "baseline_degree": 1,
    "flip_y_unit": False,
    "prominence": 0.15,
    "use_auto_prominence": False,
}


class SessionError(ValueError):
    """Invalid or unsupported session file / payload."""


@dataclass
class SessionData:
    """In-memory representation of a loaded ChemSpec session."""

    spectrum: Spectrum
    processing: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_PROCESSING))
    peaks: list[Peak] = field(default_factory=list)
    notes: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)
    source_path: str = ""
    format_version: int = SESSION_FORMAT_VERSION
    software_version: str = ""
    history: ProcessingHistory = field(default_factory=ProcessingHistory)
    raw_data_hash: str = ""
    source_path_hash: str = ""
    analysis_fingerprint: str = ""
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


def _package_version() -> str:
    try:
        from spectrum_core import __version__ as _v

        return str(_v)
    except Exception:  # noqa: BLE001
        return ""


def _canonical_float_token(v: Any) -> str:
    """Stable textual token for one array sample (null for non-finite)."""
    if v is None:
        return "null"
    try:
        f = float(v)
    except (TypeError, ValueError):
        return "null"
    if not math.isfinite(f):
        return "null"
    # Use shortest round-trip repr that JSON would accept (no NaN literals).
    return format(f, ".17g")


def canonical_xy_encoding(x: Any, y: Any) -> str:
    """Canonical ``x||y`` encoding used for ``raw_data_hash``.

    Format: ``n=<N>\nx=<tok>,...\ny=<tok>,...`` with tokens from
    :func:`_canonical_float_token`. Stable across platforms; independent of
    session timestamps / notes / provenance.
    """
    xa = list(np.asarray(x, dtype=float).reshape(-1))
    ya = list(np.asarray(y, dtype=float).reshape(-1))
    if len(xa) != len(ya):
        raise SessionError(
            f"canonical_xy_encoding length mismatch: {len(xa)} vs {len(ya)}"
        )
    x_part = ",".join(_canonical_float_token(v) for v in xa)
    y_part = ",".join(_canonical_float_token(v) for v in ya)
    return f"n={len(xa)}\nx={x_part}\ny={y_part}"


def compute_raw_data_hash(spectrum: Spectrum) -> str:
    """SHA-256 hex digest of the canonical raw x‖y encoding."""
    payload = canonical_xy_encoding(spectrum.x, spectrum.y)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_source_path_hash(source_path: str | None) -> str:
    """Optional SHA-256 of the UTF-8 source path string (empty → "")."""
    src = (source_path or "").strip()
    if not src:
        return ""
    return hashlib.sha256(src.encode("utf-8")).hexdigest()


def _history_identity_steps(
    history: ProcessingHistory | list[Any] | None,
) -> list[dict[str, Any]]:
    """History records for fingerprinting — name + params only (no timestamps)."""
    if isinstance(history, ProcessingHistory):
        steps = history.to_list()
    elif history is None:
        steps = []
    else:
        steps = ProcessingHistory.from_list(list(history)).to_list()
    out: list[dict[str, Any]] = []
    for step in steps:
        out.append(
            {
                "name": step.get("name", ""),
                "params": step.get("params") or {},
                # deliberately omit timestamp + software_note from identity
            }
        )
    return out


def compute_analysis_fingerprint(
    *,
    raw_data_hash: str,
    x_unit: str,
    y_unit: str,
    processing: dict[str, Any] | None = None,
    history: ProcessingHistory | list[Any] | None = None,
    peaks: list[Peak] | None = None,
    source_path_hash: str = "",
) -> str:
    """SHA-256 over computational identity fields (timestamps excluded).

    Identity includes: ``raw_data_hash``, **``x_unit`` / ``y_unit``** (units are
    intentionally *not* part of ``raw_data_hash``, which is arrays-only),
    normalized processing, history name/params (not timestamps), peak metric
    dicts, and optional ``source_path_hash``. Wall-clock times in ``history``
    must not change this.
    """
    proc = normalize_processing(processing)
    peak_dicts = [peak_to_dict(p) for p in (peaks or [])]
    identity = {
        "raw_data_hash": raw_data_hash,
        "source_path_hash": source_path_hash or "",
        "x_unit": x_unit,
        "y_unit": y_unit,
        "processing": proc,
        "history_steps": _history_identity_steps(history),
        "peaks": peak_dicts,
    }
    blob = json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _json_float(v: float) -> float | None:
    """Serialize floats; JSON has no NaN/Inf — map non-finite → null."""
    f = float(v)
    if not math.isfinite(f):
        return None
    return f


def _parse_float(v: Any, *, default: float = float("nan"), name: str = "value") -> float:
    if v is None:
        return float(default)
    try:
        return float(v)
    except (TypeError, ValueError) as exc:
        raise SessionError(f"invalid float for {name}: {v!r}") from exc


def _json_safe_meta(meta: dict[str, Any] | None) -> dict[str, Any]:
    """Keep only JSON-safe scalar / nested dict-list values (drop ndarrays)."""
    if not meta:
        return {}
    out: dict[str, Any] = {}
    for key, val in meta.items():
        safe = _to_jsonable(val)
        if safe is _DROP:
            continue
        out[str(key)] = safe
    return out


_DROP = object()


def _to_jsonable(val: Any) -> Any:
    if val is None or isinstance(val, (bool, int, str)):
        return val
    if isinstance(val, float):
        return _json_float(val)
    if isinstance(val, (np.floating, np.integer)):
        return _json_float(float(val))
    if isinstance(val, np.ndarray):
        return _DROP  # large / non-portable; spectrum x/y are stored explicitly
    if isinstance(val, dict):
        nested = _json_safe_meta(val)
        return nested
    if isinstance(val, (list, tuple)):
        items = []
        for item in val:
            j = _to_jsonable(item)
            if j is _DROP:
                return _DROP
            items.append(j)
        return items
    # pathlib, enums, etc.
    try:
        json.dumps(val)
        return val
    except (TypeError, ValueError):
        return str(val)


def peak_to_dict(peak: Peak) -> dict[str, Any]:
    return {
        "index": int(peak.index),
        "x": _json_float(peak.x),
        "y": _json_float(peak.y),
        "prominence": _json_float(peak.prominence),
        "fwhm": _json_float(peak.fwhm),
        "area": _json_float(peak.area),
        "width_definition": str(peak.width_definition or ""),
        "half_max_level": _json_float(peak.half_max_level),
        "left_boundary_x": _json_float(peak.left_boundary_x),
        "right_boundary_x": _json_float(peak.right_boundary_x),
        "area_definition": str(peak.area_definition or ""),
        "baseline_reference_note": str(peak.baseline_reference_note or ""),
    }


def peak_from_dict(data: dict[str, Any]) -> Peak:
    if not isinstance(data, dict):
        raise SessionError("each peak must be an object")
    try:
        index = int(data["index"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SessionError(f"peak missing/invalid index: {data!r}") from exc
    return Peak(
        index=index,
        x=_parse_float(data.get("x"), name="peak.x"),
        y=_parse_float(data.get("y"), name="peak.y"),
        prominence=_parse_float(data.get("prominence"), default=0.0, name="peak.prominence"),
        fwhm=_parse_float(data.get("fwhm"), name="peak.fwhm"),
        area=_parse_float(data.get("area"), name="peak.area"),
        width_definition=str(
            data.get("width_definition") or WIDTH_DEF_PROMINENCE_RELATIVE
        ),
        half_max_level=_parse_float(data.get("half_max_level"), name="peak.half_max_level"),
        left_boundary_x=_parse_float(
            data.get("left_boundary_x"), name="peak.left_boundary_x"
        ),
        right_boundary_x=_parse_float(
            data.get("right_boundary_x"), name="peak.right_boundary_x"
        ),
        area_definition=str(data.get("area_definition") or AREA_DEF_TRAPZ_HALF_MAX),
        baseline_reference_note=str(data.get("baseline_reference_note") or ""),
    )


def normalize_processing(processing: dict[str, Any] | None) -> dict[str, Any]:
    """Merge caller processing with defaults; coerce types."""
    out = dict(DEFAULT_PROCESSING)
    if not processing:
        return out
    if not isinstance(processing, dict):
        raise SessionError("processing must be an object")
    if "baseline_on" in processing:
        out["baseline_on"] = bool(processing["baseline_on"])
    if "baseline_method" in processing:
        method = processing["baseline_method"]
        if method is None or method == "":
            out["baseline_method"] = "polynomial"
        else:
            out["baseline_method"] = str(method)
    if "baseline_degree" in processing:
        try:
            out["baseline_degree"] = int(processing["baseline_degree"])
        except (TypeError, ValueError) as exc:
            raise SessionError(
                f"invalid baseline_degree: {processing['baseline_degree']!r}"
            ) from exc
    if "flip_y_unit" in processing:
        out["flip_y_unit"] = bool(processing["flip_y_unit"])
    if "prominence" in processing:
        out["prominence"] = _parse_float(
            processing["prominence"], default=0.15, name="prominence"
        )
    if "use_auto_prominence" in processing:
        out["use_auto_prominence"] = bool(processing["use_auto_prominence"])
    return out


def build_provenance(
    *,
    spectrum: Spectrum,
    source_path: str | None = None,
    processing: dict[str, Any] | None = None,
    peak_count: int = 0,
    package_version: str | None = None,
) -> dict[str, Any]:
    """Structured provenance snapshot stored inside the session file."""
    proc = normalize_processing(processing)
    bl = proc["baseline_method"] if proc["baseline_on"] else "none"
    src = source_path or ""
    if src:
        src_bit = Path(src).name
    elif spectrum.title:
        src_bit = spectrum.title
    else:
        src_bit = "(no source)"
    ver = package_version if package_version is not None else _package_version()
    summary_parts = [
        f"source={src_bit}",
        f"x={spectrum.x_unit}",
        f"y={spectrum.y_unit}",
        f"baseline={bl}",
        f"peaks={int(peak_count)}",
    ]
    if ver:
        summary_parts.append(f"v={ver}")
    return {
        "source": src or spectrum.title or "",
        "source_name": src_bit,
        "x_unit": spectrum.x_unit,
        "y_unit": spectrum.y_unit,
        "baseline": bl,
        "peak_count": int(peak_count),
        "package_version": ver or "",
        "title": spectrum.title or "",
        "summary": " · ".join(summary_parts),
    }


def spectrum_to_session_dict(
    spectrum: Spectrum,
    *,
    source_path: str | None = None,
) -> dict[str, Any]:
    """Embed spectrum arrays + units + title (+ original path)."""
    return {
        "x": [_json_float(float(v)) for v in np.asarray(spectrum.x, dtype=float)],
        "y": [_json_float(float(v)) for v in np.asarray(spectrum.y, dtype=float)],
        "x_unit": spectrum.x_unit,
        "y_unit": spectrum.y_unit,
        "title": spectrum.title or "",
        "source_path": source_path or str(spectrum.meta.get("source", "") or ""),
        "meta": _json_safe_meta(spectrum.meta),
    }


def spectrum_from_session_dict(data: dict[str, Any]) -> Spectrum:
    if not isinstance(data, dict):
        raise SessionError("spectrum must be an object")
    for key in ("x", "y", "x_unit", "y_unit"):
        if key not in data:
            raise SessionError(f"spectrum missing required field: {key}")
    x_raw = data["x"]
    y_raw = data["y"]
    if not isinstance(x_raw, list) or not isinstance(y_raw, list):
        raise SessionError("spectrum.x and spectrum.y must be arrays")
    if len(x_raw) != len(y_raw):
        raise SessionError(
            f"spectrum x/y length mismatch: {len(x_raw)} vs {len(y_raw)}"
        )
    if len(x_raw) == 0:
        raise SessionError("spectrum must have at least one point")
    x_unit = data["x_unit"]
    y_unit = data["y_unit"]
    if x_unit not in _X_UNITS:
        raise SessionError(f"unsupported x_unit: {x_unit!r}")
    if y_unit not in _Y_UNITS:
        raise SessionError(f"unsupported y_unit: {y_unit!r}")
    meta = data.get("meta") or {}
    if not isinstance(meta, dict):
        raise SessionError("spectrum.meta must be an object")
    meta = dict(meta)
    src = data.get("source_path") or ""
    if src and "source" not in meta:
        meta["source"] = src
    # JSON null → NaN for array points
    x = np.asarray([float("nan") if v is None else float(v) for v in x_raw], dtype=float)
    y = np.asarray([float("nan") if v is None else float(v) for v in y_raw], dtype=float)
    return Spectrum(
        x=x,
        y=y,
        x_unit=x_unit,  # type: ignore[arg-type]
        y_unit=y_unit,  # type: ignore[arg-type]
        title=str(data.get("title") or ""),
        meta=meta,
    )


def session_to_dict(
    spectrum: Spectrum,
    *,
    processing: dict[str, Any] | None = None,
    peaks: list[Peak] | None = None,
    notes: str = "",
    source_path: str | None = None,
    provenance: dict[str, Any] | None = None,
    software_version: str | None = None,
    history: ProcessingHistory | list[Any] | None = None,
    raw_data_hash: str | None = None,
    source_path_hash: str | None = None,
    analysis_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Build a current-version session payload (no I/O).

    ``spectrum`` should be the *raw* (unprocessed) spectrum. Pipeline steps are
    stored in ``history`` so callers can replay onto a working copy.

    Computational identity fields (``raw_data_hash``, optional
    ``source_path_hash``, ``analysis_fingerprint``) are computed unless
    explicitly supplied. History timestamps do not affect the fingerprint.
    """
    peaks = peaks or []
    proc = normalize_processing(processing)
    src = source_path if source_path is not None else str(
        spectrum.meta.get("source", "") or ""
    )
    ver = software_version if software_version is not None else _package_version()
    prov = provenance if provenance is not None else build_provenance(
        spectrum=spectrum,
        source_path=src,
        processing=proc,
        peak_count=len(peaks),
        package_version=ver,
    )
    if isinstance(history, ProcessingHistory):
        hist_list = history.to_list()
    elif history is None:
        hist_list = []
    else:
        hist_list = ProcessingHistory.from_list(list(history)).to_list()
    rdh = raw_data_hash if raw_data_hash is not None else compute_raw_data_hash(spectrum)
    sph = (
        source_path_hash
        if source_path_hash is not None
        else compute_source_path_hash(src)
    )
    fp = (
        analysis_fingerprint
        if analysis_fingerprint is not None
        else compute_analysis_fingerprint(
            raw_data_hash=rdh,
            x_unit=spectrum.x_unit,
            y_unit=spectrum.y_unit,
            processing=proc,
            history=hist_list,
            peaks=peaks,
            source_path_hash=sph,
        )
    )
    return {
        "format_version": SESSION_FORMAT_VERSION,
        "software_version": ver or "",
        "spectrum": spectrum_to_session_dict(spectrum, source_path=src),
        "processing": proc,
        "peaks": [peak_to_dict(p) for p in peaks],
        "notes": notes if notes is not None else "",
        "provenance": prov,
        "history": hist_list,
        "raw_data_hash": rdh,
        "source_path_hash": sph,
        "analysis_fingerprint": fp,
    }


def migrate_session_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Upgrade an older session payload to ``SESSION_FORMAT_VERSION``.

    v1 → v2: add ``raw_data_hash``, ``source_path_hash``, ``analysis_fingerprint``.
    Idempotent for already-current payloads.
    """
    if not isinstance(data, dict):
        raise SessionError("session root must be a JSON object")
    if "format_version" not in data:
        raise SessionError("missing format_version")
    try:
        ver = int(data["format_version"])
    except (TypeError, ValueError) as exc:
        raise SessionError(f"invalid format_version: {data['format_version']!r}") from exc
    if ver < SESSION_FORMAT_VERSION_MIN or ver > SESSION_FORMAT_VERSION:
        raise SessionError(
            f"unsupported format_version {ver} (this build supports "
            f"{SESSION_FORMAT_VERSION_MIN}..{SESSION_FORMAT_VERSION})"
        )
    out = dict(data)
    if ver == SESSION_FORMAT_VERSION and out.get("raw_data_hash"):
        return out

    # Ensure spectrum parses so we can hash it
    if "spectrum" not in out:
        raise SessionError("missing spectrum")
    spectrum = spectrum_from_session_dict(out["spectrum"])
    src = ""
    spec_block = out.get("spectrum") or {}
    if isinstance(spec_block, dict):
        src = str(spec_block.get("source_path") or "")
    proc = normalize_processing(out.get("processing"))
    peaks_raw = out.get("peaks") or []
    if not isinstance(peaks_raw, list):
        raise SessionError("peaks must be an array")
    peaks = [peak_from_dict(p) for p in peaks_raw]
    hist = out.get("history") or []

    rdh = out.get("raw_data_hash") or compute_raw_data_hash(spectrum)
    sph = out.get("source_path_hash")
    if sph is None or sph == "":
        sph = compute_source_path_hash(src)
    fp = out.get("analysis_fingerprint") or compute_analysis_fingerprint(
        raw_data_hash=rdh,
        x_unit=spectrum.x_unit,
        y_unit=spectrum.y_unit,
        processing=proc,
        history=hist,
        peaks=peaks,
        source_path_hash=sph,
    )
    out["raw_data_hash"] = rdh
    out["source_path_hash"] = sph
    out["analysis_fingerprint"] = fp
    out["format_version"] = SESSION_FORMAT_VERSION
    return out


def validate_session_dict(data: Any) -> dict[str, Any]:
    """Schema-check a session payload; migrate older versions; return dict."""
    if not isinstance(data, dict):
        raise SessionError("session root must be a JSON object")
    if "format_version" not in data:
        raise SessionError("missing format_version")
    try:
        ver = int(data["format_version"])
    except (TypeError, ValueError) as exc:
        raise SessionError(f"invalid format_version: {data['format_version']!r}") from exc
    if ver < SESSION_FORMAT_VERSION_MIN or ver > SESSION_FORMAT_VERSION:
        raise SessionError(
            f"unsupported format_version {ver} (this build supports "
            f"{SESSION_FORMAT_VERSION_MIN}..{SESSION_FORMAT_VERSION})"
        )
    data = migrate_session_dict(data)
    if "spectrum" not in data:
        raise SessionError("missing spectrum")
    # Eager structural checks (spectrum arrays + units)
    spectrum_from_session_dict(data["spectrum"])
    if "processing" in data and data["processing"] is not None:
        normalize_processing(data["processing"])
    if "peaks" in data and data["peaks"] is not None:
        if not isinstance(data["peaks"], list):
            raise SessionError("peaks must be an array")
        for i, p in enumerate(data["peaks"]):
            try:
                peak_from_dict(p)
            except SessionError as exc:
                raise SessionError(f"peaks[{i}]: {exc}") from exc
    if "notes" in data and data["notes"] is not None and not isinstance(data["notes"], str):
        raise SessionError("notes must be a string")
    if "provenance" in data and data["provenance"] is not None:
        if not isinstance(data["provenance"], dict):
            raise SessionError("provenance must be an object")
    if "history" in data and data["history"] is not None:
        if not isinstance(data["history"], list):
            raise SessionError("history must be an array")
        try:
            ProcessingHistory.from_list(data["history"])
        except (TypeError, ValueError) as exc:
            raise SessionError(f"invalid history: {exc}") from exc
    for key in ("raw_data_hash", "analysis_fingerprint"):
        val = data.get(key)
        if val is not None and not isinstance(val, str):
            raise SessionError(f"{key} must be a string")
    if data.get("source_path_hash") is not None and not isinstance(
        data["source_path_hash"], str
    ):
        raise SessionError("source_path_hash must be a string")
    return data


def session_from_dict(data: dict[str, Any]) -> SessionData:
    """Parse + validate a session dict into SessionData."""
    data = validate_session_dict(data)
    spectrum = spectrum_from_session_dict(data["spectrum"])
    processing = normalize_processing(data.get("processing"))
    peaks_raw = data.get("peaks") or []
    peaks = [peak_from_dict(p) for p in peaks_raw]
    notes = data.get("notes") or ""
    if not isinstance(notes, str):
        notes = str(notes)
    provenance = data.get("provenance") or {}
    if not isinstance(provenance, dict):
        provenance = {}
    source_path = ""
    spec_block = data.get("spectrum") or {}
    if isinstance(spec_block, dict):
        source_path = str(spec_block.get("source_path") or "")
    try:
        history = ProcessingHistory.from_list(data.get("history"))
    except (TypeError, ValueError) as exc:
        raise SessionError(f"invalid history: {exc}") from exc
    return SessionData(
        spectrum=spectrum,
        processing=processing,
        peaks=peaks,
        notes=notes,
        provenance=dict(provenance),
        source_path=source_path,
        format_version=int(data["format_version"]),
        software_version=str(data.get("software_version") or ""),
        history=history,
        raw_data_hash=str(data.get("raw_data_hash") or ""),
        source_path_hash=str(data.get("source_path_hash") or ""),
        analysis_fingerprint=str(data.get("analysis_fingerprint") or ""),
        raw=dict(data),
    )


def save_session(
    path: str | Path,
    spectrum: Spectrum,
    *,
    processing: dict[str, Any] | None = None,
    peaks: list[Peak] | None = None,
    notes: str = "",
    source_path: str | None = None,
    provenance: dict[str, Any] | None = None,
    software_version: str | None = None,
    history: ProcessingHistory | list[Any] | None = None,
) -> dict[str, Any]:
    """Write a ``.csw.json`` / ``.chemspec.json`` session file; return the payload."""
    path = Path(path)
    payload = session_to_dict(
        spectrum,
        processing=processing,
        peaks=peaks,
        notes=notes,
        source_path=source_path,
        provenance=provenance,
        software_version=software_version,
        history=history,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return payload


def load_session(path: str | Path) -> SessionData:
    """Load and validate a session file."""
    path = Path(path)
    if not path.is_file():
        raise SessionError(f"session file not found: {path}")
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SessionError(f"invalid JSON in session file: {exc}") from exc
    except OSError as exc:
        raise SessionError(f"could not read session file: {exc}") from exc
    return session_from_dict(data)


def session_download_filename(title: str | None = None) -> str:
    """Safe download basename for a session file (``.csw.json``)."""
    stem = (title or "").strip()
    if not stem:
        return "session.csw.json"
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in stem)
    return f"{safe}.csw.json"


# Re-export unit aliases for type checkers / callers
__all__ = [
    "SESSION_FORMAT_VERSION",
    "SESSION_FORMAT_VERSION_MIN",
    "SESSION_EXTENSIONS",
    "DEFAULT_PROCESSING",
    "SessionError",
    "SessionData",
    "save_session",
    "load_session",
    "session_to_dict",
    "session_from_dict",
    "validate_session_dict",
    "migrate_session_dict",
    "build_provenance",
    "peak_to_dict",
    "peak_from_dict",
    "normalize_processing",
    "spectrum_to_session_dict",
    "spectrum_from_session_dict",
    "session_download_filename",
    "canonical_xy_encoding",
    "compute_raw_data_hash",
    "compute_source_path_hash",
    "compute_analysis_fingerprint",
    "ProcessingHistory",
    "XUnit",
    "YUnit",
]
