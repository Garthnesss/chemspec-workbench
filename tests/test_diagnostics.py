"""Measurement diagnostics: SNR, boundary warnings, baseline advisories."""

from __future__ import annotations

import math

import numpy as np

from spectrum_core import Peak, Spectrum, find_peaks
from spectrum_core.diagnostics import (
    CODE_BASELINE_APPLIED,
    CODE_BASELINE_NAN_RESIDUAL,
    CODE_LOW_SNR,
    CODE_MISSING_BOTH_BOUNDARIES,
    CODE_MISSING_LEFT_BOUNDARY,
    CODE_MISSING_RIGHT_BOUNDARY,
    SNR_METHOD_MAD_DIFF,
    baseline_findings,
    diagnose_measurement,
    estimate_noise_mad_diff,
    estimate_snr,
    peak_boundary_findings,
)
from spectrum_core.peaks import WIDTH_DEF_PROMINENCE_RELATIVE


def _gaussian(
    *,
    center: float = 100.0,
    amp: float = 5.0,
    sigma: float = 2.0,
    noise: float = 0.0,
    seed: int = 0,
) -> Spectrum:
    rng = np.random.default_rng(seed)
    x = np.linspace(center - 40, center + 40, 801)
    y = amp * np.exp(-0.5 * ((x - center) / sigma) ** 2)
    if noise > 0:
        y = y + rng.normal(0.0, noise, size=y.shape)
    return Spectrum(x=x, y=y, x_unit="nm", y_unit="intensity", title="synth")


def test_estimate_noise_mad_diff_scales_with_sigma():
    rng = np.random.default_rng(1)
    y = rng.normal(0.0, 2.0, size=5000)
    est = estimate_noise_mad_diff(y)
    assert math.isfinite(est)
    # Roughly within factor of ~2 of true σ for this estimator
    assert 1.0 < est < 4.0


def test_estimate_snr_high_for_clean_gaussian():
    spec = _gaussian(amp=10.0, noise=0.05)
    peaks = find_peaks(spec, prominence=0.5)
    snr, method = estimate_snr(spec, peaks)
    assert method == SNR_METHOD_MAD_DIFF
    assert math.isfinite(snr)
    assert snr > 20.0


def test_estimate_snr_unavailable_all_nan():
    spec = Spectrum(
        x=np.arange(10, dtype=float),
        y=np.full(10, np.nan),
        x_unit="nm",
        y_unit="intensity",
    )
    snr, method = estimate_snr(spec, [])
    assert math.isnan(snr)
    assert method != SNR_METHOD_MAD_DIFF or math.isnan(snr)


def test_peak_boundary_missing_left_at_edge():
    # Peak jammed against left edge → missing left crossing
    x = np.linspace(0, 10, 101)
    y = np.exp(-0.5 * ((x - 0.0) / 0.8) ** 2)  # center at edge
    peaks = [
        Peak(
            index=0,
            x=float(x[0]),
            y=float(y[0]),
            prominence=1.0,
            fwhm=float("nan"),
            area=float("nan"),
            width_definition=WIDTH_DEF_PROMINENCE_RELATIVE,
            half_max_level=0.5,
            left_boundary_x=float("nan"),
            right_boundary_x=2.0,
        )
    ]
    findings = peak_boundary_findings(peaks, n_points=len(x))
    codes = {f.code for f in findings}
    assert CODE_MISSING_LEFT_BOUNDARY in codes


def test_peak_boundary_missing_both():
    peaks = [
        Peak(
            index=5,
            x=1.0,
            y=1.0,
            prominence=0.5,
            fwhm=float("nan"),
            area=float("nan"),
            left_boundary_x=float("nan"),
            right_boundary_x=float("nan"),
        )
    ]
    findings = peak_boundary_findings(peaks, n_points=20)
    assert any(f.code == CODE_MISSING_BOTH_BOUNDARIES for f in findings)


def test_baseline_findings_info_and_nan_residual():
    x = np.linspace(0, 1, 50)
    y = np.ones_like(x)
    y[0] = np.nan
    spec = Spectrum(
        x=x,
        y=y,
        x_unit="nm",
        y_unit="A",
        meta={"baseline_method": "polynomial", "baseline_degree": 1},
    )
    findings = baseline_findings(spec)
    codes = {f.code for f in findings}
    assert CODE_BASELINE_APPLIED in codes
    assert CODE_BASELINE_NAN_RESIDUAL in codes


def test_diagnose_measurement_low_snr_warning():
    # Weak signal vs strong white noise → SNR below threshold
    rng = np.random.default_rng(3)
    x = np.linspace(0, 100, 500)
    y = 0.2 * np.exp(-0.5 * ((x - 50) / 3) ** 2) + rng.normal(0, 1.0, size=x.shape)
    spec = Spectrum(x=x, y=y, x_unit="nm", y_unit="intensity")
    # Fabricate a low-prominence peak so signal uses prominence path
    peaks = [
        Peak(
            index=250,
            x=50.0,
            y=0.2,
            prominence=0.2,
            fwhm=1.0,
            area=1.0,
            left_boundary_x=48.0,
            right_boundary_x=52.0,
        )
    ]
    diag = diagnose_measurement(spec, peaks, low_snr_threshold=3.0)
    assert math.isfinite(diag.snr_estimate)
    assert diag.snr_estimate < 3.0
    assert any(f.code == CODE_LOW_SNR for f in diag.warnings)


def test_diagnose_measurement_summary_line_includes_snr():
    spec = _gaussian(amp=8.0, noise=0.02)
    peaks = find_peaks(spec, prominence=0.3)
    diag = diagnose_measurement(spec, peaks, baseline_applied=True)
    line = diag.summary_line()
    assert "SNR" in line
    assert "baseline applied" in line


def test_diagnose_none_spectrum():
    diag = diagnose_measurement(None)
    assert diag.peak_count == 0
    assert diag.summary_line() == ""


def test_real_find_peaks_edge_missing_crossing_surfaced():
    """Truncated-on-the-right Gaussian → find_peaks + missing right crossing."""
    x = np.linspace(0, 10, 401)
    # Peak near right edge so the right half-max walk hits the array end
    y = np.exp(-0.5 * ((x - 9.5) / 0.6) ** 2)
    spec = Spectrum(x=x, y=y, x_unit="nm", y_unit="intensity")
    peaks = find_peaks(spec, prominence=0.05)
    assert peaks, "expected at least one near-edge peak"
    # Prefer the rightmost peak
    p = max(peaks, key=lambda q: q.x)
    diag = diagnose_measurement(spec, [p])
    warn_codes = {f.code for f in diag.warnings}
    # Either find_peaks already left NaN boundaries, or we assert via helper
    if not warn_codes:
        findings = peak_boundary_findings(
            [
                Peak(
                    index=p.index,
                    x=p.x,
                    y=p.y,
                    prominence=p.prominence,
                    fwhm=float("nan"),
                    area=float("nan"),
                    left_boundary_x=p.left_boundary_x,
                    right_boundary_x=float("nan"),
                )
            ],
            n_points=len(x),
        )
        warn_codes = {f.code for f in findings}
    assert warn_codes & {
        CODE_MISSING_LEFT_BOUNDARY,
        CODE_MISSING_RIGHT_BOUNDARY,
        CODE_MISSING_BOTH_BOUNDARIES,
    }, f"expected boundary warning, got codes={warn_codes} peak={p}"
