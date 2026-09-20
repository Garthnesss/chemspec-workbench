"""3-D surface grid from folder / stacked spectra."""

from pathlib import Path

import numpy as np
import pytest

from spectrum_core import (
    folder_waterfall,
    ingest_folder,
    spectra_to_surface,
)
from spectrum_core.spectrum import Spectrum
from spectrum_core.viz3d import SurfaceGrid


def test_surface_from_waterfall_fixture_strips_stack_offset():
    root = Path(__file__).resolve().parents[1] / "fixtures" / "waterfall"
    raw = ingest_folder(
        root,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    stacked = folder_waterfall(
        root,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
        offset=1.0,
    )
    grid = spectra_to_surface(stacked)
    assert isinstance(grid, SurfaceGrid)
    assert grid.series_kind == "series_index"
    assert grid.z.shape == (3, len(raw[0].x))
    assert not grid.resampled
    np.testing.assert_allclose(grid.z[0], raw[0].y)
    np.testing.assert_allclose(grid.z[1], raw[1].y)
    np.testing.assert_allclose(grid.z[2], raw[2].y)
    np.testing.assert_array_equal(grid.series, [0.0, 1.0, 2.0])


def test_surface_requires_two_traces():
    spec = Spectrum(x=[1.0, 2.0], y=[0.1, 0.2], x_unit="nm", y_unit="A")
    with pytest.raises(ValueError, match="at least two"):
        spectra_to_surface([spec])


def test_surface_rejects_mismatched_y_unit():
    a = Spectrum(x=[1.0, 2.0], y=[0.1, 0.2], x_unit="nm", y_unit="A")
    b = Spectrum(x=[1.0, 2.0], y=[0.1, 0.2], x_unit="nm", y_unit="intensity")
    with pytest.raises(ValueError, match="y_unit"):
        spectra_to_surface([a, b])


def test_surface_resamples_uneven_x():
    a = Spectrum(x=[400.0, 500.0, 600.0], y=[0.0, 1.0, 0.0], x_unit="nm", y_unit="A")
    b = Spectrum(x=[450.0, 550.0], y=[0.5, 0.5], x_unit="nm", y_unit="A")
    grid = spectra_to_surface([a, b], n_x=5)
    assert grid.resampled
    assert grid.z.shape == (2, 5)
    assert grid.x[0] == pytest.approx(450.0)
    assert grid.x[-1] == pytest.approx(550.0)


def test_surface_no_overlap_raises():
    a = Spectrum(x=[1.0, 2.0], y=[0.1, 0.2], x_unit="nm", y_unit="A")
    b = Spectrum(x=[10.0, 11.0], y=[0.1, 0.2], x_unit="nm", y_unit="A")
    with pytest.raises(ValueError, match="overlapping"):
        spectra_to_surface([a, b])
