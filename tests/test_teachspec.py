"""TeachSpec Phase-0: calibration, mock frame → Spectrum (no hardware)."""

from __future__ import annotations

import json

import numpy as np
import pytest

from spectrum_core import find_peaks
from teachspec import (
    OpticalLiveFrame,
    fit_wavelength_calibration,
    frame_to_spectrum,
    generate_mock_frame,
    load_calibration,
    save_calibration,
)
from teachspec.calibration import WavelengthCalibration


def test_linear_pixel_to_nm_fit_correctness():
    # Perfect line: nm = 0.5 * pixel + 400
    pixels = [100.0, 200.0, 300.0]
    wavelengths = [450.0, 500.0, 550.0]
    cal = fit_wavelength_calibration(pixels, wavelengths, fit_kind="linear")
    assert cal.fit_kind == "linear"
    assert len(cal.coefficients) == 2
    pred = cal.pixel_to_nm(pixels)
    np.testing.assert_allclose(pred, wavelengths, rtol=0, atol=1e-9)
    assert cal.rmse_nm is not None and cal.rmse_nm < 1e-9


def test_quadratic_fit_with_three_points():
    pixels = [0.0, 100.0, 200.0]
    # nm = 0.001 p^2 + 0.5 p + 400
    wavelengths = [0.001 * p**2 + 0.5 * p + 400.0 for p in pixels]
    cal = fit_wavelength_calibration(pixels, wavelengths, fit_kind="quadratic")
    assert cal.fit_kind == "quadratic"
    assert len(cal.coefficients) == 3
    pred = cal.pixel_to_nm(pixels)
    np.testing.assert_allclose(pred, wavelengths, rtol=0, atol=1e-6)


def test_fit_rejects_single_point():
    with pytest.raises(ValueError, match="≥2"):
        fit_wavelength_calibration([10.0], [450.0], fit_kind="linear")


def test_fit_rejects_duplicate_pixels():
    with pytest.raises(ValueError, match="duplicate"):
        fit_wavelength_calibration([10.0, 10.0], [450.0, 500.0], fit_kind="linear")


def test_quadratic_needs_three_points():
    with pytest.raises(ValueError, match="≥3"):
        fit_wavelength_calibration([10.0, 20.0], [450.0, 500.0], fit_kind="quadratic")


def test_calibration_save_load_roundtrip(tmp_path):
    cal = fit_wavelength_calibration(
        [50.0, 150.0, 250.0],
        [420.0, 520.0, 620.0],
        fit_kind="linear",
        meta={"label": "unit-test"},
    )
    path = tmp_path / "cal.json"
    save_calibration(cal, path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["format"] == "teachspec.calibration"
    assert raw["format_version"] == 1
    loaded = load_calibration(path)
    assert loaded.fit_kind == cal.fit_kind
    np.testing.assert_allclose(loaded.coefficients, cal.coefficients)
    assert loaded.known_lines == cal.known_lines
    assert loaded.meta.get("label") == "unit-test"
    np.testing.assert_allclose(
        loaded.pixel_to_nm([100.0]), cal.pixel_to_nm([100.0])
    )


def test_mock_frame_to_spectrum_roundtrip_peaks():
    frame, truth = generate_mock_frame(
        n_pixels=512,
        noise_std=0.005,
        sigma_pixels=2.0,
        seed=7,
    )
    assert frame.meta["synthetic"] is True
    a, b = truth["linear_coefficients"]
    lines = truth["lines_nm"]
    pixels = [(wl - b) / a for wl in lines]
    cal = fit_wavelength_calibration(pixels, lines, fit_kind="linear")
    spec = frame_to_spectrum(frame, cal)
    assert spec.x_unit == "nm"
    assert spec.y_unit == "intensity"
    assert len(spec) == 512
    assert spec.meta.get("synthetic") is True
    peaks = find_peaks(spec, prominence=0.2)
    peak_nm = [p.x for p in peaks]
    for wl in lines:
        assert any(abs(x - wl) < 3.0 for x in peak_nm), (
            f"missing mock line near {wl} nm; peaks={peak_nm}"
        )


def test_optical_live_frame_bad_shape():
    with pytest.raises(ValueError, match="1-D"):
        OpticalLiveFrame(intensity=np.zeros((4, 4)))
    with pytest.raises(ValueError, match="at least one"):
        OpticalLiveFrame(intensity=np.array([]))


def test_wavelength_calibration_coeff_validation():
    with pytest.raises(ValueError, match="exactly 2"):
        WavelengthCalibration(coefficients=[1.0, 2.0, 3.0], fit_kind="linear")
