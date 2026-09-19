"""A ↔ %T conversion helpers."""

import math

import numpy as np
import pytest

from spectrum_core import (
    Spectrum,
    absorbance_to_percent_t,
    can_convert_y,
    convert_spectrum_y,
    percent_t_to_absorbance,
)


def test_a_to_percent_t_known_values():
    a = np.array([0.0, 1.0, 2.0])
    t = absorbance_to_percent_t(a)
    np.testing.assert_allclose(t, [100.0, 10.0, 1.0], rtol=1e-10)


def test_percent_t_to_a_roundtrip():
    a = np.array([0.0, 0.3, 1.0, 2.5])
    t = absorbance_to_percent_t(a)
    back = percent_t_to_absorbance(t)
    np.testing.assert_allclose(back, a, rtol=1e-10)


def test_invalid_percent_t_becomes_nan():
    t = np.array([100.0, 0.0, -5.0, np.nan])
    a = percent_t_to_absorbance(t)
    assert math.isclose(a[0], 0.0, abs_tol=1e-12)
    assert np.isnan(a[1]) and np.isnan(a[2]) and np.isnan(a[3])


def test_nonfinite_absorbance_becomes_nan():
    a = np.array([1.0, np.inf, np.nan])
    t = absorbance_to_percent_t(a)
    assert math.isclose(t[0], 10.0, rel_tol=1e-10)
    assert np.isnan(t[1]) and np.isnan(t[2])


def test_convert_spectrum_a_to_percent_t():
    spec = Spectrum(x=[1.0, 2.0], y=[0.0, 1.0], x_unit="nm", y_unit="A", title="t")
    out = convert_spectrum_y(spec, "percent_T")
    assert out.y_unit == "percent_T"
    np.testing.assert_allclose(out.y, [100.0, 10.0])
    assert out.meta["y_unit_converted_from"] == "A"
    assert spec.y_unit == "A"  # original unchanged


def test_convert_spectrum_same_unit_is_copy():
    spec = Spectrum(x=[1.0], y=[0.5], y_unit="A")
    out = convert_spectrum_y(spec, "A")
    assert out.y_unit == "A"
    np.testing.assert_allclose(out.y, spec.y)
    assert out is not spec


def test_convert_intensity_raises():
    spec = Spectrum(x=[1.0], y=[1.0], y_unit="intensity")
    with pytest.raises(ValueError, match="intensity"):
        convert_spectrum_y(spec, "A")


def test_convert_target_intensity_raises():
    spec = Spectrum(x=[1.0], y=[1.0], y_unit="A")
    with pytest.raises(ValueError, match="target"):
        convert_spectrum_y(spec, "intensity")  # type: ignore[arg-type]


def test_percent_t_over_100_noted():
    spec = Spectrum(x=[1.0, 2.0], y=[100.0, 120.0], y_unit="percent_T")
    out = convert_spectrum_y(spec, "A")
    assert "conversion_notes" in out.meta
    assert any("100" in n for n in out.meta["conversion_notes"])
    assert out.y[1] < 0  # A negative when %T > 100


def test_can_convert_y():
    assert can_convert_y("A") is True
    assert can_convert_y("percent_T") is True
    assert can_convert_y("intensity") is False
