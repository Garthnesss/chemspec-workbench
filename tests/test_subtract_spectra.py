"""Named-blank subtraction (user labels the reference; not auto-detect)."""

import numpy as np
import pytest

from spectrum_core import Spectrum, subtract_spectra
from spectrum_core.errors import ProcessingError


def test_subtract_blank_same_grid():
    sample = Spectrum(x=[1.0, 2.0, 3.0], y=[1.0, 2.0, 3.0], x_unit="nm", y_unit="A")
    blank = Spectrum(x=[1.0, 2.0, 3.0], y=[0.5, 0.5, 0.5], x_unit="nm", y_unit="A", title="blank")
    out = subtract_spectra(sample, blank, role="blank")
    np.testing.assert_allclose(out.y, [0.5, 1.5, 2.5])
    assert out.meta["subtract_role"] == "blank"
    assert "not_auto_detected" in out.meta["honesty"]


def test_subtract_rejects_unit_mismatch():
    a = Spectrum(x=[1.0, 2.0], y=[1.0, 2.0], x_unit="nm", y_unit="A")
    b = Spectrum(x=[1.0, 2.0], y=[1.0, 2.0], x_unit="cm-1", y_unit="A")
    with pytest.raises(ProcessingError, match="x_unit"):
        subtract_spectra(a, b)


def test_subtract_no_extrapolation():
    sample = Spectrum(x=[1.0, 2.0, 5.0], y=[1.0, 1.0, 1.0], x_unit="nm", y_unit="A")
    blank = Spectrum(x=[1.0, 2.0], y=[0.2, 0.2], x_unit="nm", y_unit="A")
    out = subtract_spectra(sample, blank)
    assert np.isfinite(out.y[0])
    assert np.isnan(out.y[-1])
