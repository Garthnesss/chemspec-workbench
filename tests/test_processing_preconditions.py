"""Processing op preconditions raise clear ProcessingError messages."""

from __future__ import annotations

import numpy as np
import pytest

from spectrum_core import (
    ProcessingError,
    Spectrum,
    SpectrumError,
    apply_step,
    op_baseline,
    op_despike,
    op_normalize,
    op_smooth,
)


def _spec(n: int = 50) -> Spectrum:
    x = np.linspace(400.0, 700.0, n)
    y = 0.1 + 0.5 * np.exp(-0.5 * ((x - 550.0) / 20.0) ** 2)
    return Spectrum(x=x, y=y, x_unit="nm", y_unit="A", title="precond")


def test_smooth_rejects_even_window_with_processing_error() -> None:
    with pytest.raises(ProcessingError, match="odd"):
        op_smooth(_spec(), window_length=10, polyorder=2)


def test_smooth_rejects_polyorder_ge_window() -> None:
    with pytest.raises(ProcessingError, match="polyorder must be < window_length"):
        op_smooth(_spec(), window_length=5, polyorder=5)


def test_smooth_rejects_window_longer_than_spectrum() -> None:
    with pytest.raises(ProcessingError, match="cannot exceed spectrum length"):
        op_smooth(_spec(n=9), window_length=11, polyorder=2)


def test_smooth_rejects_short_spectrum() -> None:
    with pytest.raises(ProcessingError, match="length .* must be >= 3"):
        op_smooth(_spec(n=2), window_length=3, polyorder=1)


def test_despike_rejects_even_window() -> None:
    with pytest.raises(ProcessingError, match="odd"):
        op_despike(_spec(), window=4, z_thresh=5.0)


def test_despike_rejects_nonpositive_z() -> None:
    with pytest.raises(ProcessingError, match="z_thresh"):
        op_despike(_spec(), window=5, z_thresh=0.0)


def test_despike_rejects_window_longer_than_spectrum() -> None:
    with pytest.raises(ProcessingError, match="cannot exceed spectrum length"):
        op_despike(_spec(n=5), window=7, z_thresh=4.0)


def test_normalize_rejects_unknown_mode() -> None:
    with pytest.raises(ProcessingError, match="unknown mode"):
        op_normalize(_spec(), mode="l2")


def test_baseline_rejects_negative_degree() -> None:
    with pytest.raises(ProcessingError, match="degree must be >= 0"):
        op_baseline(_spec(), method="polynomial", degree=-1)


def test_baseline_rejects_degree_too_high_for_length() -> None:
    with pytest.raises(ProcessingError, match="need more than"):
        op_baseline(_spec(n=3), method="polynomial", degree=5)


def test_apply_step_unknown_is_processing_error() -> None:
    with pytest.raises(ProcessingError, match="unknown pipeline step"):
        apply_step(_spec(), None, "fft")


def test_processing_error_is_spectrum_error_and_value_error() -> None:
    with pytest.raises(SpectrumError):
        op_smooth(_spec(), window_length=8, polyorder=2)
    with pytest.raises(ValueError):
        op_smooth(_spec(), window_length=8, polyorder=2)
