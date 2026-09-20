"""Peak detection and characterization (scipy.signal.find_peaks wrapper).

FWHM and area (measurement contract)
------------------------------------
After locating peaks with ``scipy.signal.find_peaks``, each peak is characterized
and the contract is recorded on :class:`Peak` (``width_definition``,
``half_max_level``, ``left_boundary_x`` / ``right_boundary_x``,
``area_definition``, optional ``baseline_reference_note``).

**Half-maximum level (prominence-relative).** With prominence ``P`` from scipy
(or ``0`` if absent), the half-max ordinate is::

    y_half = y_peak - 0.5 * P

That matches SciPy ``peak_widths(..., rel_height=0.5)``: the reference
“baseline” under the peak is ``y_peak - P``. **This is not** absolute
half-of-peak-above-zero (``0.5 * y_peak``) unless prominence is zero / missing,
in which case we fall back to ``y_half = 0.5 * y_peak`` (zero-baseline
assumption, appropriate for isolated synthetic Gaussians). The chosen
definition is stored in ``Peak.width_definition`` /
``Peak.baseline_reference_note``.

**FWHM.** Walk left/right in *index* space from the peak until ``y`` drops to
or below ``y_half`` (NaN samples are treated as below half-max so they stop
the walk). Linearly interpolate the crossing abscissae on each side. Then
``fwhm = abs(x_right - x_left)``. Absolute value makes ascending and
descending ``x`` (e.g. IR ``cm-1``) equivalent. Boundaries are stored as
``left_boundary_x`` / ``right_boundary_x``. If either side cannot form a
crossing, ``fwhm`` and both boundaries are ``nan``.

**Area.** Trapezoidal integral of ``y`` between the same half-max abscissae
used for FWHM (endpoints included at ``y_half``). Uses ``numpy.trapezoid``
with the real ``x`` sample spacing (uneven ``dx`` is honored). The result is
wrapped in ``abs(...)`` so descending ``x`` still yields a positive physical
area. ``area_definition`` records this. If FWHM boundaries are missing,
``area`` is ``nan``.

This is *not* compound identification — only geometric peak metrics on the
loaded trace.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks as _scipy_find_peaks

from spectrum_core.spectrum import Spectrum

# Stable contract strings stored on Peak / CSV / session JSON.
WIDTH_DEF_PROMINENCE_RELATIVE = "prominence_relative_half_height"
WIDTH_DEF_ZERO_BASELINE = "zero_baseline_half_of_peak"
AREA_DEF_TRAPZ_HALF_MAX = "trapz_between_half_max_bounds"

BASELINE_NOTE_PROMINENCE = (
    "half-max at y_peak - 0.5*prominence (SciPy peak_widths rel_height=0.5 style); "
    "not absolute half-of-peak-above-zero"
)
BASELINE_NOTE_ZERO = (
    "prominence missing/zero → fallback half-max at 0.5*y_peak (zero baseline)"
)


@dataclass(frozen=True)
class Peak:
    """A detected peak with FWHM / area and an explicit measurement contract."""

    index: int
    x: float
    y: float
    prominence: float
    fwhm: float = float("nan")
    area: float = float("nan")
    width_definition: str = WIDTH_DEF_PROMINENCE_RELATIVE
    half_max_level: float = float("nan")
    left_boundary_x: float = float("nan")
    right_boundary_x: float = float("nan")
    area_definition: str = AREA_DEF_TRAPZ_HALF_MAX
    baseline_reference_note: str = ""


def _finite(v: float) -> bool:
    return bool(np.isfinite(v))


def _half_max_level(y_peak: float, prominence: float) -> tuple[float, str, str]:
    """Return ``(y_half, width_definition, baseline_reference_note)``."""
    if prominence > 0 and _finite(prominence):
        return (
            y_peak - 0.5 * prominence,
            WIDTH_DEF_PROMINENCE_RELATIVE,
            BASELINE_NOTE_PROMINENCE,
        )
    return (
        0.5 * y_peak,
        WIDTH_DEF_ZERO_BASELINE,
        BASELINE_NOTE_ZERO,
    )


def _crossing_x(
    x: np.ndarray,
    y: np.ndarray,
    i_hi: int,
    i_lo: int,
    y_half: float,
) -> float:
    """Linear interpolate ``x`` where ``y`` crosses ``y_half`` between samples.

    ``i_hi`` is the sample on the peak side (``y > y_half``); ``i_lo`` is the
    neighbor at or below half-max.
    """
    y_hi = float(y[i_hi])
    y_lo = float(y[i_lo])
    if not (_finite(y_hi) and _finite(y_lo)):
        return float("nan")
    if y_hi == y_lo:
        return float(x[i_hi])
    t = (y_half - y_hi) / (y_lo - y_hi)
    # Crossing should lie on the segment; allow tiny numeric slop.
    if t < -1e-9 or t > 1.0 + 1e-9:
        return float("nan")
    t = min(max(t, 0.0), 1.0)
    return float(x[i_hi]) + t * (float(x[i_lo]) - float(x[i_hi]))


def _half_max_bounds(
    x: np.ndarray,
    y: np.ndarray,
    peak_idx: int,
    y_half: float,
) -> tuple[float, float, int, int]:
    """Return ``(x_left, x_right, i_left, i_right)`` at half-max.

    ``i_left`` / ``i_right`` are the outermost indices still strictly above
    ``y_half`` (inclusive of the peak). Missing crossings yield ``nan``.
    """
    n = len(y)
    y_peak = float(y[peak_idx])
    if not _finite(y_peak) or y_peak < y_half:
        return float("nan"), float("nan"), peak_idx, peak_idx

    i_l = peak_idx
    while i_l > 0:
        y_prev = float(y[i_l - 1])
        if not _finite(y_prev) or y_prev <= y_half:
            break
        i_l -= 1

    if i_l > 0 and _finite(float(y[i_l - 1])) and float(y[i_l - 1]) <= y_half:
        x_left = _crossing_x(x, y, i_l, i_l - 1, y_half)
    else:
        x_left = float("nan")

    i_r = peak_idx
    while i_r < n - 1:
        y_next = float(y[i_r + 1])
        if not _finite(y_next) or y_next <= y_half:
            break
        i_r += 1

    if i_r < n - 1 and _finite(float(y[i_r + 1])) and float(y[i_r + 1]) <= y_half:
        x_right = _crossing_x(x, y, i_r, i_r + 1, y_half)
    else:
        x_right = float("nan")

    return x_left, x_right, i_l, i_r


def _fwhm_and_area(
    x: np.ndarray,
    y: np.ndarray,
    peak_idx: int,
    prominence: float,
) -> tuple[float, float, float, float, float, str, str]:
    """Compute FWHM, area, half-max level, and boundaries for one peak.

    Returns
    -------
    fwhm, area, half_max_level, left_boundary_x, right_boundary_x,
    width_definition, baseline_reference_note
    """
    y_peak = float(y[peak_idx])
    if not _finite(y_peak):
        return (
            float("nan"),
            float("nan"),
            float("nan"),
            float("nan"),
            float("nan"),
            WIDTH_DEF_PROMINENCE_RELATIVE,
            BASELINE_NOTE_PROMINENCE,
        )
    y_half, width_def, note = _half_max_level(y_peak, prominence)
    if not _finite(y_half):
        return (
            float("nan"),
            float("nan"),
            float("nan"),
            float("nan"),
            float("nan"),
            width_def,
            note,
        )

    x_left, x_right, i_l, i_r = _half_max_bounds(x, y, peak_idx, y_half)
    if not (_finite(x_left) and _finite(x_right)):
        return float("nan"), float("nan"), y_half, x_left, x_right, width_def, note

    fwhm = abs(x_right - x_left)
    if fwhm == 0.0:
        return 0.0, 0.0, y_half, x_left, x_right, width_def, note

    xs: list[float] = [x_left]
    ys: list[float] = [y_half]
    for i in range(i_l, i_r + 1):
        yi = float(y[i])
        if _finite(yi):
            xs.append(float(x[i]))
            ys.append(yi)
    xs.append(x_right)
    ys.append(y_half)

    area = float(
        abs(np.trapezoid(np.asarray(ys, dtype=float), np.asarray(xs, dtype=float)))
    )
    return fwhm, area, y_half, x_left, x_right, width_def, note


def find_peaks(
    spectrum: Spectrum,
    *,
    prominence: float | None = None,
    height: float | None = None,
    distance: int | None = None,
    width: float | None = None,
) -> list[Peak]:
    """Find peaks on ``spectrum.y`` using ``scipy.signal.find_peaks``.

    ``prominence`` defaults to 10% of the y-range when not provided, so
    fixtures with clear Gaussians are found without tuning.

    Each returned :class:`Peak` includes **FWHM** and **area** characterized
    at the prominence-relative half-maximum (see module docstring), plus
    explicit contract fields (``width_definition``, ``half_max_level``,
    boundaries, ``area_definition``). Metrics are ``nan`` when crossings
    cannot be resolved (edges, NaNs, flat traces).

    Returns peaks sorted by descending prominence.
    """
    y = spectrum.y
    x = spectrum.x
    if prominence is None:
        finite = y[np.isfinite(y)]
        if finite.size == 0:
            return []
        y_range = float(np.nanmax(finite) - np.nanmin(finite))
        prominence = 0.1 * y_range if y_range > 0 else None

    kwargs: dict = {}
    if prominence is not None:
        kwargs["prominence"] = prominence
    if height is not None:
        kwargs["height"] = height
    if distance is not None:
        kwargs["distance"] = distance
    if width is not None:
        kwargs["width"] = width

    # Replace NaNs with a low sentinel so find_peaks does not treat them as
    # peaks; characterization still stops at NaNs via _half_max_bounds.
    y_for_find = np.asarray(y, dtype=float).copy()
    nan_mask = ~np.isfinite(y_for_find)
    if nan_mask.any():
        fill = float(np.nanmin(y_for_find[~nan_mask])) if (~nan_mask).any() else 0.0
        y_for_find[nan_mask] = fill - abs(fill) - 1.0

    indices, props = _scipy_find_peaks(y_for_find, **kwargs)
    prominences = props.get("prominences")
    peaks: list[Peak] = []
    for i, idx in enumerate(indices):
        prom = float(prominences[i]) if prominences is not None else 0.0
        if not _finite(prom):
            prom = 0.0
        fwhm, area, y_half, x_left, x_right, width_def, note = _fwhm_and_area(
            x, y, int(idx), prom
        )
        peaks.append(
            Peak(
                index=int(idx),
                x=float(spectrum.x[idx]),
                y=float(spectrum.y[idx]),
                prominence=prom,
                fwhm=fwhm,
                area=area,
                width_definition=width_def,
                half_max_level=y_half,
                left_boundary_x=x_left,
                right_boundary_x=x_right,
                area_definition=AREA_DEF_TRAPZ_HALF_MAX,
                baseline_reference_note=note,
            )
        )
    peaks.sort(key=lambda p: p.prominence, reverse=True)
    return peaks
