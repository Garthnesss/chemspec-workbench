"""FID/NMR NiceGUI playground: helpers + build_ui smoke (no magnet, no server)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

_UI_APP = Path(__file__).resolve().parents[1] / "fidnmr" / "ui_app.py"


def test_ui_app_source_avoids_removed_banner() -> None:
    src = _UI_APP.read_text(encoding="utf-8")
    assert "ui.banner" not in src
    assert "ui.card" in src
    assert "_BANNER_TEXT" in src
    assert "compound" in src.lower()
    assert "magnet" in src.lower()


def test_state_rebuild_ppm_and_hz() -> None:
    from fidnmr.ui_app import FidNmrUiState

    state = FidNmrUiState()
    assert state.fid is not None
    assert state.spectrum is not None
    assert state.spectrum.x_unit == "ppm"
    assert len(state.peaks) >= 1
    n_ppm = len(state.spectrum)

    state.x_unit = "Hz"
    state.rebuild_spectrum()
    assert state.spectrum is not None
    assert state.spectrum.x_unit == "Hz"
    assert len(state.spectrum) == n_ppm

    state.phc0_deg = 90.0
    state.rebuild_spectrum()
    assert state.spectrum is not None
    assert abs(float(state.spectrum.meta["fidnmr"]["phc0_deg"]) - 90.0) < 1e-9


def test_figures_without_nicegui_server() -> None:
    pytest.importorskip("plotly")
    from fidnmr.ui_app import FidNmrUiState, fid_time_figure, spectrum_figure

    state = FidNmrUiState()
    tfig = fid_time_figure(state)
    assert len(tfig.data) == 2
    assert len(tfig.data[0].x) == state.fid.npts
    np.testing.assert_allclose(tfig.data[0].y, np.real(state.fid.signal))

    sfig = spectrum_figure(state)
    assert sfig.data
    assert len(sfig.data[0].x) == len(state.spectrum)
    assert "ppm" in str(sfig.layout.xaxis.title.text).lower()


def test_build_ui_smoke_without_server() -> None:
    pytest.importorskip("nicegui")
    from nicegui import ui

    assert hasattr(ui, "card")
    assert hasattr(ui, "plotly")
    assert not hasattr(ui, "banner")

    from fidnmr.ui_app import _BANNER_TEXT, build_ui

    assert "educational" in _BANNER_TEXT.lower()
    assert "compound" in _BANNER_TEXT.lower()
    state = build_ui()
    assert state.spectrum is not None
    assert state.fid is not None
    assert state.x_unit == "ppm"
