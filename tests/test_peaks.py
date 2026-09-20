"""Peak finder: fixture locations + FWHM/area on synthetic Gaussians."""

from __future__ import annotations

import math

import numpy as np
import pytest

from spectrum_core import Peak, Spectrum, find_peaks, ingest_csv
from spectrum_core.peaks import _fwhm_and_area


def _peak_xs(spec, prominence=0.15):
    return [p.x for p in find_peaks(spec, prominence=prominence)]


def test_uvvis_peaks_near_280_and_350(uvvis_csv):
    spec = ingest_csv(
        uvvis_csv,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    xs = _peak_xs(spec, prominence=0.15)
    assert any(abs(x - 280) <= 8 for x in xs), f"no ~280 nm peak in {xs}"
    assert any(abs(x - 350) <= 10 for x in xs), f"no ~350 nm peak in {xs}"


def test_ir_peaks_near_1700_and_2900(ir_csv):
    spec = ingest_csv(
        ir_csv,
        x_col="wavenumber_cm-1",
        y_col="intensity",
        x_unit="cm-1",
        y_unit="intensity",
    )
    xs = _peak_xs(spec, prominence=0.15)
    assert any(abs(x - 1700) <= 30 for x in xs), f"no ~1700 cm-1 peak in {xs}"
    assert any(abs(x - 2900) <= 40 for x in xs), f"no ~2900 cm-1 peak in {xs}"


def _gaussian_spectrum(
    *,
    center: float = 0.0,
    amp: float = 1.0,
    sigma: float = 1.0,
    x: np.ndarray | None = None,
    x_unit: str = "nm",
    descending: bool = False,
) -> tuple[Spectrum, float, float]:
    """Build an isolated Gaussian; return spectrum, expected FWHM, expected half-max area."""
    if x is None:
        x = np.linspace(center - 8 * sigma, center + 8 * sigma, 2001)
    if descending:
        x = x[::-1].copy()
    y = amp * np.exp(-0.5 * ((x - center) / sigma) ** 2)
    spec = Spectrum(x=x, y=y, x_unit=x_unit, y_unit="intensity", title="synth gaussian")
    # Analytic FWHM for Gaussian: 2 * sqrt(2 ln 2) * sigma
    fwhm_true = 2.0 * math.sqrt(2.0 * math.log(2.0)) * sigma
    # Area between half-max bounds = amp * sigma * sqrt(2π) * erf(sqrt(ln 2))
    area_total = amp * sigma * math.sqrt(2.0 * math.pi)
    area_fwhm = area_total * math.erf(math.sqrt(math.log(2.0)))
    return spec, fwhm_true, area_fwhm


def test_gaussian_fwhm_and_area_ascending():
    sigma = 2.5
    amp = 1.8
    spec, fwhm_true, area_true = _gaussian_spectrum(
        center=100.0, amp=amp, sigma=sigma, x_unit="nm"
    )
    peaks = find_peaks(spec, prominence=0.05 * amp)
    assert len(peaks) >= 1
    p = max(peaks, key=lambda q: q.y)
    assert abs(p.x - 100.0) < 0.05
    assert abs(p.fwhm - fwhm_true) / fwhm_true < 0.02  # 2%
    assert abs(p.area - area_true) / area_true < 0.03  # 3%


def test_gaussian_fwhm_and_area_descending_x():
    """IR-like descending x: FWHM/area must stay positive and match analytics."""
    sigma = 3.0
    amp = 1.0
    spec, fwhm_true, area_true = _gaussian_spectrum(
        center=1700.0,
        amp=amp,
        sigma=sigma,
        x=np.linspace(1700.0 - 10 * sigma, 1700.0 + 10 * sigma, 2501),
        x_unit="cm-1",
        descending=True,
    )
    assert spec.x[0] > spec.x[-1]
    peaks = find_peaks(spec, prominence=0.05)
    assert len(peaks) >= 1
    p = max(peaks, key=lambda q: q.y)
    assert abs(p.x - 1700.0) < 0.1
    assert p.fwhm > 0 and p.area > 0
    assert abs(p.fwhm - fwhm_true) / fwhm_true < 0.02
    assert abs(p.area - area_true) / area_true < 0.03


def test_fwhm_nan_when_peak_at_array_edge():
    """Peak sample at index 0 cannot form a left half-max crossing → nan."""
    # scipy.find_peaks often skips true edge samples; characterize index 0 directly.
    x = np.linspace(0, 10, 101)
    y = np.exp(-0.5 * ((x - 0.0) / 1.2) ** 2)
    fwhm, area, *_rest = _fwhm_and_area(x, y, peak_idx=0, prominence=float(y[0]))
    assert math.isnan(fwhm)
    assert math.isnan(area)


def test_nan_gap_stops_half_max_walk():
    """NaN samples interrupt the half-max walk (NaN-safe)."""
    x = np.linspace(-10, 10, 401)
    y = np.exp(-0.5 * (x / 1.5) ** 2)
    # Punch NaNs on both flanks inside the half-max region so crossings fail.
    y = y.copy()
    y[(x > -2.0) & (x < -1.5)] = np.nan
    y[(x > 1.5) & (x < 2.0)] = np.nan
    spec = Spectrum(x=x, y=y, x_unit="nm", y_unit="intensity")
    peaks = find_peaks(spec, prominence=0.1)
    assert peaks
    p = peaks[0]
    assert abs(p.x) < 0.1
    # With NaNs cutting both sides before true half-max, FWHM should be nan.
    assert math.isnan(p.fwhm)
    assert math.isnan(p.area)


def test_peak_dataclass_defaults_allow_legacy_construction():
    p = Peak(index=1, x=2.0, y=3.0, prominence=0.5)
    assert math.isnan(p.fwhm)
    assert math.isnan(p.area)


def test_prominence_relative_differs_from_zero_baseline_on_slope():
    """Sloping continuum: prominence-relative half-max ≠ 0.5 * y_peak."""
    x = np.linspace(0.0, 40.0, 801)
    # Linear baseline + Gaussian so scipy prominence < y_peak.
    baseline = 0.02 * x
    amp = 1.0
    sigma = 1.5
    center = 20.0
    y = baseline + amp * np.exp(-0.5 * ((x - center) / sigma) ** 2)
    spec = Spectrum(x=x, y=y, x_unit="nm", y_unit="A", title="slope+gauss")
    peaks = find_peaks(spec, prominence=0.2)
    assert peaks
    p = max(peaks, key=lambda q: q.y)
    assert abs(p.x - center) < 0.2
    assert p.width_definition == "prominence_relative_half_height"
    assert p.area_definition == "trapz_between_half_max_bounds"
    assert "prominence" in p.baseline_reference_note.lower()
    # Prominence-relative half-max sits above 0.5 * y_peak on a positive slope.
    zero_half = 0.5 * p.y
    assert p.half_max_level == pytest.approx(p.y - 0.5 * p.prominence)
    assert p.half_max_level > zero_half + 0.05
    assert math.isfinite(p.left_boundary_x) and math.isfinite(p.right_boundary_x)
    assert p.fwhm == pytest.approx(abs(p.right_boundary_x - p.left_boundary_x))


def test_missing_crossing_keeps_nan_boundaries():
    x = np.linspace(0, 10, 101)
    y = np.exp(-0.5 * ((x - 0.0) / 1.2) ** 2)
    fwhm, area, y_half, x_left, x_right, width_def, _note = _fwhm_and_area(
        x, y, peak_idx=0, prominence=float(y[0])
    )
    assert math.isnan(fwhm) and math.isnan(area)
    assert math.isfinite(y_half)
    assert math.isnan(x_left)  # no left flank
    assert width_def == "prominence_relative_half_height"


def test_descending_ir_contract_boundaries_ordered_in_index_space():
    """Descending cm-1: boundaries finite; fwhm uses abs(dx)."""
    sigma = 3.0
    amp = 1.0
    spec, fwhm_true, _area_true = _gaussian_spectrum(
        center=1700.0,
        amp=amp,
        sigma=sigma,
        x=np.linspace(1700.0 - 10 * sigma, 1700.0 + 10 * sigma, 2501),
        x_unit="cm-1",
        descending=True,
    )
    peaks = find_peaks(spec, prominence=0.05)
    p = max(peaks, key=lambda q: q.y)
    assert math.isfinite(p.left_boundary_x) and math.isfinite(p.right_boundary_x)
    # Index-walk left/right: on descending x, left_boundary_x > right_boundary_x.
    assert p.left_boundary_x > p.right_boundary_x
    assert p.fwhm == pytest.approx(abs(p.right_boundary_x - p.left_boundary_x))
    assert abs(p.fwhm - fwhm_true) / fwhm_true < 0.02


def test_uneven_spacing_area_uses_real_dx():
    """Trapezoid area must honor uneven Δx (not assume uniform grid)."""
    # Build a triangular peak on uneven x; analytic area via trapz on same points.
    x = np.array([0.0, 1.0, 1.5, 2.0, 4.0, 5.0], dtype=float)
    y = np.array([0.0, 0.0, 2.0, 0.0, 0.0, 0.0], dtype=float)
    # Peak at index 2, y=2. Force prominence=2 → y_half=1.0.
    # Crossings: between idx1–2 (y 0→2) at x=1.25; between 2–3 (2→0) at x=1.75.
    fwhm, area, y_half, x_left, x_right, _wd, _note = _fwhm_and_area(
        x, y, peak_idx=2, prominence=2.0
    )
    assert y_half == pytest.approx(1.0)
    assert x_left == pytest.approx(1.25)
    assert x_right == pytest.approx(1.75)
    assert fwhm == pytest.approx(0.5)
    # Manual trapz with endpoints at half-max: [1.25,1],[1.5,2],[1.75,1]
    expected = abs(np.trapezoid([1.0, 2.0, 1.0], [1.25, 1.5, 1.75]))
    assert area == pytest.approx(expected)
    # Contrast: if someone wrongly used index-uniform dx=1, area would differ.
    wrong_uniform = abs(np.trapezoid([1.0, 2.0, 1.0], [0.0, 1.0, 2.0]))
    assert area != pytest.approx(wrong_uniform)


def test_peak_contract_fields_defaults():
    p = Peak(index=1, x=2.0, y=3.0, prominence=0.5)
    assert p.width_definition == "prominence_relative_half_height"
    assert p.area_definition == "trapz_between_half_max_bounds"
    assert math.isnan(p.half_max_level)
    assert math.isnan(p.left_boundary_x)
    assert math.isnan(p.right_boundary_x)
