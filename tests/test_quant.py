"""Quantitative helpers — geometry on loaded traces, not ID."""

from __future__ import annotations

import numpy as np
import pytest

from spectrum_core import (
    ProcessingError,
    Spectrum,
    apply_step,
    band_integral,
    beer_lambert_c,
    compare_spectra,
    convert_spectrum_x,
    crossings,
    derivative_spectrum,
    nm_to_wavenumber,
    series_stats,
    wavenumber_to_nm,
)


def _gauss(x, mu=550.0, sig=12.0, amp=1.0):
    return amp * np.exp(-0.5 * ((x - mu) / sig) ** 2)


def test_nm_cm1_roundtrip():
    nm = np.array([250.0, 400.0, 1000.0])
    cm1 = nm_to_wavenumber(nm)
    np.testing.assert_allclose(cm1, [40000.0, 25000.0, 10000.0])
    np.testing.assert_allclose(wavenumber_to_nm(cm1), nm)


def test_convert_spectrum_x_sorts_ascending():
    spec = Spectrum(
        x=np.array([400.0, 500.0, 250.0]),
        y=np.array([0.1, 0.2, 0.3]),
        x_unit="nm",
        y_unit="A",
    )
    out = convert_spectrum_x(spec, "cm-1")
    assert out.x_unit == "cm-1"
    assert np.all(np.diff(out.x) >= 0)
    assert spec.x_unit == "nm"


def test_derivative_finite_and_logged():
    x = np.linspace(0.0, 10.0, 101)
    spec = Spectrum(x=x, y=2.0 * x + 1.0, x_unit="nm", y_unit="A")
    d1 = derivative_spectrum(spec, order=1, window_length=11, polyorder=2)
    assert np.all(np.isfinite(d1.y))
    assert d1.meta["derivative_order"] == 1
    assert not np.allclose(d1.y, spec.y)


def test_band_integral_known_rectangle():
    x = np.linspace(0.0, 10.0, 101)
    y = np.ones_like(x)
    spec = Spectrum(x=x, y=y, x_unit="nm", y_unit="A")
    band = band_integral(spec, 2.0, 6.0, linear_ends=False)
    assert band.area == pytest.approx(4.0, rel=1e-3)


def test_compare_identical_is_zero_rmse():
    x = np.linspace(400.0, 700.0, 80)
    spec = Spectrum(x=x, y=_gauss(x), x_unit="nm", y_unit="A", title="a")
    other = Spectrum(x=x, y=_gauss(x), x_unit="nm", y_unit="A", title="b")
    cmp_ = compare_spectra(spec, other)
    assert cmp_.rmse == pytest.approx(0.0, abs=1e-12)
    assert cmp_.pearson_r == pytest.approx(1.0)


def test_compare_rejects_unit_mismatch():
    a = Spectrum(x=[1.0, 2.0, 3.0], y=[0.1, 0.2, 0.3], x_unit="nm", y_unit="A")
    b = Spectrum(x=[1.0, 2.0, 3.0], y=[0.1, 0.2, 0.3], x_unit="cm-1", y_unit="A")
    with pytest.raises(ProcessingError, match="x_unit"):
        compare_spectra(a, b)


def test_series_stats_mean():
    x = np.linspace(0, 1, 11)
    specs = [
        Spectrum(x=x, y=np.ones_like(x) * k, x_unit="nm", y_unit="A")
        for k in (1.0, 3.0, 5.0)
    ]
    st = series_stats(specs)
    np.testing.assert_allclose(st["mean"], 3.0)
    assert st["n_series"] == 3


def test_beer_lambert_user_constants():
    assert beer_lambert_c(0.5, 1000.0, 1.0) == pytest.approx(5.0e-4)


def test_beer_lambert_rejects_zero_path():
    with pytest.raises(ProcessingError):
        beer_lambert_c(0.5, 1000.0, 0.0)


def test_crossings_two_gaussians():
    x = np.linspace(400.0, 700.0, 301)
    a = Spectrum(x=x, y=_gauss(x, 500, 20, 1.0), x_unit="nm", y_unit="A")
    b = Spectrum(x=x, y=_gauss(x, 600, 20, 1.0), x_unit="nm", y_unit="A")
    xs = crossings(a, b)
    assert xs
    assert min(xs) == pytest.approx(550.0, abs=2.0)


def test_pipeline_derivative_step():
    x = np.linspace(0, 10, 51)
    spec = Spectrum(x=x, y=np.sin(x), x_unit="nm", y_unit="intensity")
    out, hist = apply_step(
        spec, None, "derivative", {"order": 1, "window_length": 7, "polyorder": 3}
    )
    assert hist.steps[-1].name == "derivative"
    assert out.meta["derivative_order"] == 1
