"""Quantitative helpers on loaded traces. Not compound identification.

- nm \u2194 cm-1 conversion
- Savitzky\u2013Golay derivatives
- user-window band integral (optional linear end baseline)
- compare two traces on a shared x-grid
- series mean / std
- Beer\u2013Lambert c from A with *user-supplied* \u03b5 and path
- sign-change crossings (not isosbestic assignment)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.signal import savgol_filter

from spectrum_core.errors import ProcessingError
from spectrum_core.ingest import ensure_ascending_x
from spectrum_core.spectrum import Spectrum, XUnit

NM_CM1 = 1.0e7  # nm \u00b7 cm-1


def nm_to_wavenumber(nm: np.ndarray | float) -> np.ndarray:
    arr = np.asarray(nm, dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    ok = np.isfinite(arr) & (arr != 0.0)
    out[ok] = NM_CM1 / arr[ok]
    return out


def wavenumber_to_nm(cm1: np.ndarray | float) -> np.ndarray:
    arr = np.asarray(cm1, dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    ok = np.isfinite(arr) & (arr != 0.0)
    out[ok] = NM_CM1 / arr[ok]
    return out


def convert_spectrum_x(spectrum: Spectrum, target: XUnit) -> Spectrum:
    if target not in ("nm", "cm-1"):
        raise ProcessingError(
            f"convert_spectrum_x: target must be 'nm' or 'cm-1' (got {target!r})"
        )
    src = spectrum.x_unit
    if src == target:
        return spectrum.copy()
    if {src, target} != {"nm", "cm-1"}:
        raise ProcessingError(
            f"convert_spectrum_x: cannot convert {src!r} \u2192 {target!r} "
            "(optical nm \u2194 cm-1 only)"
        )
    if src == "nm":
        x_new = nm_to_wavenumber(spectrum.x)
    else:
        x_new = wavenumber_to_nm(spectrum.x)
    out = Spectrum(
        x=x_new,
        y=np.asarray(spectrum.y, dtype=float).copy(),
        x_unit=target,
        y_unit=spectrum.y_unit,
        title=spectrum.title,
        meta={
            **spectrum.meta,
            "x_unit_converted_from": src,
            "x_convert": "nm_cm-1_1e7",
        },
    )
    return ensure_ascending_x(out)


def derivative_spectrum(
    spectrum: Spectrum,
    *,
    order: int = 1,
    window_length: int = 11,
    polyorder: int = 3,
) -> Spectrum:
    try:
        n = int(order)
        wl = int(window_length)
        po = int(polyorder)
    except (TypeError, ValueError) as exc:
        raise ProcessingError(
            "derivative: order, window_length, polyorder must be integers"
        ) from exc
    if n not in (1, 2):
        raise ProcessingError(f"derivative: order must be 1 or 2 (got {n})")
    if wl < 3 or wl % 2 == 0:
        raise ProcessingError(
            f"derivative: window_length must be odd and >= 3 (got {wl})"
        )
    if po < n:
        raise ProcessingError(
            f"derivative: polyorder ({po}) must be >= derivative order ({n})"
        )
    if po >= wl:
        raise ProcessingError(
            f"derivative: polyorder must be < window_length ({po} >= {wl})"
        )
    if wl > len(spectrum):
        raise ProcessingError(
            f"derivative: window_length ({wl}) > spectrum length ({len(spectrum)})"
        )
    y = np.asarray(spectrum.y, dtype=float)
    deriv = savgol_filter(y, window_length=wl, polyorder=po, deriv=n)
    out = spectrum.with_y(deriv, title=(spectrum.title + f" (d{n})").strip())
    out.meta = {
        **spectrum.meta,
        "derivative_order": n,
        "derivative_method": "savgol",
        "derivative_window_length": wl,
        "derivative_polyorder": po,
        "honesty": "derivative_of_loaded_trace_not_assignment",
    }
    return out


@dataclass(frozen=True)
class BandIntegral:
    x_lo: float
    x_hi: float
    area: float
    n_points: int
    subtracted_linear_ends: bool
    x_unit: str
    y_unit: str
    note: str = "trapezoid on loaded y; not compound ID"


def band_integral(
    spectrum: Spectrum,
    x_lo: float,
    x_hi: float,
    *,
    linear_ends: bool = True,
) -> BandIntegral:
    lo, hi = float(x_lo), float(x_hi)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi == lo:
        raise ProcessingError("band_integral: need finite x_lo != x_hi")
    if lo > hi:
        lo, hi = hi, lo
    x = np.asarray(spectrum.x, dtype=float)
    y = np.asarray(spectrum.y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y) & (x >= lo) & (x <= hi)
    if int(np.count_nonzero(mask)) < 2:
        raise ProcessingError(
            "band_integral: need \u22652 finite points inside the window"
        )
    xs = x[mask]
    ys = y[mask]
    order = np.argsort(xs)
    xs, ys = xs[order], ys[order]
    if linear_ends:
        y0, y1 = float(ys[0]), float(ys[-1])
        x0, x1 = float(xs[0]), float(xs[-1])
        if x1 != x0:
            base = y0 + (y1 - y0) * (xs - x0) / (x1 - x0)
            ys = ys - base
    area = float(np.trapezoid(ys, xs))
    return BandIntegral(
        x_lo=lo,
        x_hi=hi,
        area=area,
        n_points=int(xs.size),
        subtracted_linear_ends=bool(linear_ends),
        x_unit=spectrum.x_unit,
        y_unit=spectrum.y_unit,
    )


def _interp_onto(sample: Spectrum, reference: Spectrum) -> np.ndarray:
    sx = np.asarray(sample.x, dtype=float)
    rx = np.asarray(reference.x, dtype=float)
    ry = np.asarray(reference.y, dtype=float)
    order = np.argsort(rx)
    rx, ry = rx[order], ry[order]
    if rx.size > 1:
        uniq = np.concatenate(([True], np.diff(rx) != 0))
        rx, ry = rx[uniq], ry[uniq]
    if rx.size < 2:
        raise ProcessingError("compare_spectra: reference needs \u22652 unique x")
    return np.interp(sx, rx, ry, left=np.nan, right=np.nan)


@dataclass(frozen=True)
class CompareResult:
    n: int
    rmse: float
    mae: float
    pearson_r: float
    cosine: float
    note: str = "resampled onto sample x; comparison not identification"


def compare_spectra(sample: Spectrum, other: Spectrum) -> CompareResult:
    if sample.x_unit != other.x_unit:
        raise ProcessingError(
            f"compare_spectra: x_unit mismatch {sample.x_unit!r} vs {other.x_unit!r}"
        )
    if sample.y_unit != other.y_unit:
        raise ProcessingError(
            f"compare_spectra: y_unit mismatch {sample.y_unit!r} vs {other.y_unit!r}"
        )
    b = _interp_onto(sample, other)
    a = np.asarray(sample.y, dtype=float)
    ok = np.isfinite(a) & np.isfinite(b)
    n = int(np.count_nonzero(ok))
    if n < 3:
        raise ProcessingError("compare_spectra: need \u22653 overlapping finite points")
    aa, bb = a[ok], b[ok]
    diff = aa - bb
    rmse = float(np.sqrt(np.mean(diff * diff)))
    mae = float(np.mean(np.abs(diff)))
    if np.std(aa) == 0 or np.std(bb) == 0:
        r = float("nan")
    else:
        r = float(np.corrcoef(aa, bb)[0, 1])
    na = float(np.linalg.norm(aa))
    nb = float(np.linalg.norm(bb))
    cosine = float(np.dot(aa, bb) / (na * nb)) if na > 0 and nb > 0 else float("nan")
    return CompareResult(n=n, rmse=rmse, mae=mae, pearson_r=r, cosine=cosine)


def series_stats(spectra: list[Spectrum]) -> dict[str, Any]:
    if len(spectra) < 2:
        raise ProcessingError("series_stats: need \u22652 spectra")
    first = spectra[0]
    rows = [np.asarray(first.y, dtype=float)]
    for s in spectra[1:]:
        if s.x_unit != first.x_unit or s.y_unit != first.y_unit:
            raise ProcessingError("series_stats: units must match the first trace")
        rows.append(_interp_onto(first, s))
    z = np.vstack(rows)
    return {
        "n_series": int(z.shape[0]),
        "n_x": int(z.shape[1]),
        "mean": np.nanmean(z, axis=0),
        "std": np.nanstd(z, axis=0, ddof=1) if z.shape[0] > 1 else np.zeros(z.shape[1]),
        "x": np.asarray(first.x, dtype=float).copy(),
        "x_unit": first.x_unit,
        "y_unit": first.y_unit,
        "honesty": "stats_of_loaded_traces_not_id",
    }


def beer_lambert_c(
    absorbance: float,
    epsilon: float,
    path_cm: float,
) -> float:
    a, eps, ell = float(absorbance), float(epsilon), float(path_cm)
    if not np.isfinite(a) or not np.isfinite(eps) or not np.isfinite(ell):
        raise ProcessingError("beer_lambert_c: A, \u03b5, path must be finite")
    if eps == 0.0 or ell == 0.0:
        raise ProcessingError("beer_lambert_c: \u03b5 and path must be non-zero")
    return a / (eps * ell)


def crossings(a: Spectrum, b: Spectrum) -> list[float]:
    if a.x_unit != b.x_unit or a.y_unit != b.y_unit:
        raise ProcessingError("crossings: units must match")
    delta = np.asarray(a.y, dtype=float) - _interp_onto(a, b)
    x = np.asarray(a.x, dtype=float)
    out: list[float] = []
    for i in range(len(delta) - 1):
        d0, d1 = delta[i], delta[i + 1]
        if not np.isfinite(d0) or not np.isfinite(d1):
            continue
        if d0 == 0.0:
            out.append(float(x[i]))
        elif d0 * d1 < 0:
            t = d0 / (d0 - d1)
            out.append(float(x[i] + t * (x[i + 1] - x[i])))
    return out
