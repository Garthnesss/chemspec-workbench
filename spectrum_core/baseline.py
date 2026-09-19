"""Baseline correction: polynomial (always) + optional pybaselines methods."""

from __future__ import annotations

from typing import Any

import numpy as np

from spectrum_core.spectrum import Spectrum

# Built-in method (no extra deps)
METHOD_POLYNOMIAL = "polynomial"

# Optional pybaselines (BSD-3) method names exposed by this package
METHOD_ASLS = "asls"
METHOD_MPLS = "mpls"

PYBASELINES_METHODS: tuple[str, ...] = (METHOD_ASLS, METHOD_MPLS)
ALL_BASELINE_METHODS: tuple[str, ...] = (METHOD_POLYNOMIAL, *PYBASELINES_METHODS)

_PYBASELINES_IMPORT_HINT = (
    'Install optional support with: pip install -e ".[baselines]" '
    '(or pip install -e ".[ui,baselines]" for UI + baselines).'
)


def has_pybaselines() -> bool:
    """Return True if the optional ``pybaselines`` package is importable."""
    try:
        import pybaselines  # noqa: F401
    except ImportError:
        return False
    return True


def available_baseline_methods() -> list[str]:
    """Methods usable right now (polynomial always; pybaselines if installed)."""
    methods = [METHOD_POLYNOMIAL]
    if has_pybaselines():
        methods.extend(PYBASELINES_METHODS)
    return methods


def _require_pybaselines(method: str) -> Any:
    try:
        from pybaselines import Baseline
    except ImportError as exc:  # pragma: no cover - exercised when extra missing
        raise ImportError(
            f"Baseline method {method!r} requires the optional pybaselines "
            f"package (BSD-3). {_PYBASELINES_IMPORT_HINT}"
        ) from exc
    return Baseline


def baseline_polynomial(
    spectrum: Spectrum,
    *,
    degree: int = 2,
    mask: np.ndarray | None = None,
) -> Spectrum:
    """Fit a polynomial to ``spectrum`` and return continuum-subtracted copy.

    Parameters
    ----------
    spectrum :
        Input spectrum.
    degree :
        Polynomial degree (default 2).
    mask :
        Optional boolean mask of points used for the fit (True = use).
        When None, all finite points are used.

    Returns
    -------
    Spectrum
        Same x / units; y is original minus fitted baseline.
        Fitted baseline is stored in ``meta['baseline']``.
    """
    if degree < 0:
        raise ValueError("degree must be >= 0")

    x = spectrum.x
    y = spectrum.y
    finite = np.isfinite(x) & np.isfinite(y)
    if mask is not None:
        mask = np.asarray(mask, dtype=bool)
        if mask.shape != y.shape:
            raise ValueError("mask shape must match y")
        use = finite & mask
    else:
        use = finite

    if int(np.count_nonzero(use)) <= degree:
        raise ValueError(
            f"need more than {degree} points to fit degree-{degree} baseline"
        )

    coeffs = np.polyfit(x[use], y[use], degree)
    baseline = np.polyval(coeffs, x)
    corrected = spectrum.with_y(
        y - baseline,
        title=(spectrum.title + " (baseline corrected)").strip(),
    )
    corrected.meta = {
        **spectrum.meta,
        "baseline": baseline,
        "baseline_method": METHOD_POLYNOMIAL,
        "baseline_degree": degree,
        "baseline_coeffs": coeffs,
    }
    return corrected


def _finite_xy(spectrum: Spectrum) -> tuple[np.ndarray, np.ndarray]:
    """Return x, y copies; raise if any non-finite values (pybaselines needs clean data)."""
    x = np.asarray(spectrum.x, dtype=float)
    y = np.asarray(spectrum.y, dtype=float)
    if not (np.isfinite(x).all() and np.isfinite(y).all()):
        raise ValueError(
            "pybaselines methods require finite x and y (no NaN/Inf); "
            "clean the spectrum or use method='polynomial'"
        )
    return x, y


def _apply_pybaselines(
    spectrum: Spectrum,
    method: str,
    *,
    lam: float,
    p: float,
    half_window: int | None,
) -> Spectrum:
    Baseline = _require_pybaselines(method)
    x, y = _finite_xy(spectrum)
    fitter = Baseline(x_data=x)

    if method == METHOD_ASLS:
        baseline, params = fitter.asls(y, lam=lam, p=p)
    elif method == METHOD_MPLS:
        kwargs: dict[str, Any] = {"lam": lam, "p": p}
        if half_window is not None:
            kwargs["half_window"] = half_window
        baseline, params = fitter.mpls(y, **kwargs)
    else:  # pragma: no cover - guarded by caller
        raise ValueError(f"unknown pybaselines method: {method!r}")

    corrected = spectrum.with_y(
        y - baseline,
        title=(spectrum.title + " (baseline corrected)").strip(),
    )
    meta = {
        **spectrum.meta,
        "baseline": np.asarray(baseline, dtype=float),
        "baseline_method": method,
        "baseline_lam": lam,
        "baseline_p": p,
    }
    if half_window is not None:
        meta["baseline_half_window"] = half_window
    # Keep a small, serializable subset of pybaselines params (no huge arrays beyond baseline)
    if isinstance(params, dict) and "half_window" in params:
        meta["baseline_half_window"] = int(params["half_window"])
    corrected.meta = meta
    return corrected


def baseline_correct(
    spectrum: Spectrum,
    method: str = METHOD_POLYNOMIAL,
    *,
    degree: int = 2,
    mask: np.ndarray | None = None,
    lam: float = 1e6,
    p: float = 0.01,
    half_window: int | None = None,
) -> Spectrum:
    """Correct baseline using ``method`` (polynomial default / fallback).

    Parameters
    ----------
    spectrum :
        Input spectrum.
    method :
        ``"polynomial"`` (always available), or a pybaselines method such as
        ``"asls"`` / ``"mpls"`` when the optional ``[baselines]`` extra is installed.
    degree :
        Polynomial degree (polynomial only).
    mask :
        Optional fit mask (polynomial only).
    lam, p :
        AsLS / MPLS smoothing and asymmetry parameters (pybaselines methods).
    half_window :
        Optional morphological half-window for MPLS; ``None`` lets pybaselines optimize.

    Returns
    -------
    Spectrum
        Continuum-subtracted copy; fitted baseline in ``meta['baseline']``.

    Raises
    ------
    ImportError
        If a pybaselines method is requested but ``pybaselines`` is not installed.
    ValueError
        If ``method`` is unknown or inputs are invalid for the chosen algorithm.
    """
    key = (method or METHOD_POLYNOMIAL).strip().lower()
    if key == METHOD_POLYNOMIAL:
        return baseline_polynomial(spectrum, degree=degree, mask=mask)
    if key in PYBASELINES_METHODS:
        return _apply_pybaselines(
            spectrum, key, lam=lam, p=p, half_window=half_window
        )
    known = ", ".join(ALL_BASELINE_METHODS)
    raise ValueError(
        f"unknown baseline method {method!r}; known: {known}. "
        f"Available now: {available_baseline_methods()}"
    )
