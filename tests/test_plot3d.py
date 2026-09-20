"""Plotly 3-D surface helper + NiceGUI waterfall view_3d wiring."""

from __future__ import annotations

from pathlib import Path

import pytest

from chemspec.plot3d import build_surface_figure
from chemspec.ui_app import WorkbenchState, _build_figure, _load_waterfall_folder
from chemspec.ui_helpers import WATERFALL_FIXTURE_DIR, axis_label
from spectrum_core.spectrum import Spectrum


def test_build_surface_figure_from_waterfall_fixture() -> None:
    from spectrum_core import folder_waterfall

    stacked = folder_waterfall(
        WATERFALL_FIXTURE_DIR,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    xlabel, ylabel = axis_label("nm", "A")
    fig = build_surface_figure(stacked, xlabel, ylabel)
    assert len(fig.data) == 1
    assert fig.data[0].type == "surface"
    title = str(fig.layout.title.text)
    assert "series index" in title.lower() or "not time" in title.lower()
    assert "Series index" in str(fig.layout.scene.yaxis.title.text)
    # Honesty annotation present
    texts = [a.text for a in (fig.layout.annotations or [])]
    assert any("not a time" in t.lower() or "compound" in t.lower() for t in texts)


def test_build_surface_figure_warns_on_single_trace() -> None:
    spec = Spectrum(x=[1.0, 2.0], y=[0.1, 0.2], x_unit="nm", y_unit="A")
    fig = build_surface_figure([spec], "nm", "A")
    assert len(fig.data) == 0
    assert "unavailable" in str(fig.layout.title.text).lower()
    texts = [a.text for a in (fig.layout.annotations or [])]
    assert any("two" in t.lower() or "at least" in t.lower() for t in texts)


def test_workbench_view_3d_default_false() -> None:
    state = WorkbenchState()
    assert state.view_3d is False


def test_build_figure_uses_surface_when_view_3d() -> None:
    state = WorkbenchState()
    state.x_col = "wavelength_nm"
    state.y_col = "absorbance"
    state.x_unit = "nm"
    state.y_unit = "A"
    _load_waterfall_folder(state, WATERFALL_FIXTURE_DIR)
    assert state.error == ""
    assert len(state.waterfall) >= 2

    fig_2d = _build_figure(state)
    assert fig_2d.data[0].type == "scatter"

    state.view_3d = True
    fig_3d = _build_figure(state)
    assert fig_3d.data[0].type == "surface"
    assert "not time" in str(fig_3d.layout.title.text).lower() or "series" in str(
        fig_3d.layout.title.text
    ).lower()


def test_build_figure_warns_view_3d_with_one_trace() -> None:
    state = WorkbenchState()
    state.waterfall_mode = True
    state.view_3d = True
    state.waterfall = [
        Spectrum(
            x=[400.0, 500.0],
            y=[0.1, 0.2],
            x_unit="nm",
            y_unit="A",
            title="solo",
        )
    ]
    fig = _build_figure(state)
    assert fig.data[0].type == "scatter"
    assert "≥2" in str(fig.layout.title.text) or "3-D" in str(fig.layout.title.text)
