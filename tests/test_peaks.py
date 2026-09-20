"""Peak finder: fixture locations + FWHM/area on synthetic Gaussians."""

from __future__ import annotations

import math

import numpy as np

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
    fwhm, area = _fwhm_and_area(x, y, peak_idx=0, prominence=float(y[0]))
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
