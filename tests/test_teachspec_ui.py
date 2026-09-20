"""TeachSpec NiceGUI preview: helpers + build_ui smoke (no camera, no server)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

_UI_APP = Path(__file__).resolve().parents[1] / "teachspec" / "ui_app.py"


def test_ui_app_source_avoids_removed_banner() -> None:
    src = _UI_APP.read_text(encoding="utf-8")
    assert "ui.banner" not in src
    assert "ui.card" in src
    assert "_BANNER_TEXT" in src
    assert "SAFETY.md" in src
    assert "compound" in src.lower()


def test_intensity_figure_from_mock_without_nicegui_server() -> None:
    """Mock frame → Plotly figure data (importorskip plotly; no ui.run)."""
    pytest.importorskip("plotly")
    from teachspec.mock_source import generate_mock_frame
    from teachspec.ui_app import intensity_figure, read_mock_frame, stream_tick
    from teachspec.ui_app import TeachSpecUiState

    frame = read_mock_frame(seed=7, n_pixels=128)
    assert frame.intensity.shape == (128,)
    assert frame.meta.get("synthetic") is True

    fig = intensity_figure(frame.intensity, source_label="mock")
    assert fig.data
    assert len(fig.data[0].x) == 128
    np.testing.assert_allclose(fig.data[0].x, np.arange(128))
    np.testing.assert_allclose(fig.data[0].y, frame.intensity)
    assert "pixel" in str(fig.layout.xaxis.title.text).lower()

    empty = intensity_figure(None)
    assert empty.layout.annotations

    state = TeachSpecUiState()
    out = stream_tick(state)
    assert out.intensity.size >= 8
    assert state.frame_index == 1
    assert state.mode == "mock"

    frame2, _ = generate_mock_frame(n_pixels=64, seed=1)
    fig2 = intensity_figure(frame2.intensity)
    assert len(fig2.data[0].y) == 64


def test_intensity_figure_uses_loaded_calibration_nm_axis(tmp_path) -> None:
    pytest.importorskip("plotly")
    from teachspec.calibration import fit_wavelength_calibration, save_calibration
    from teachspec.ui_app import (
        TeachSpecUiState,
        intensity_figure,
        load_preview_calibration,
        preview_axis,
        read_mock_frame,
    )

    cal = fit_wavelength_calibration(
        [0.0, 100.0],
        [400.0, 500.0],
        fit_kind="linear",
        meta={"label": "ui-preview-test"},
    )
    path = tmp_path / "cal.json"
    save_calibration(cal, path)

    frame = read_mock_frame(seed=1, n_pixels=64)
    x_nm, xlabel = preview_axis(frame.intensity, cal)
    assert "nm" in xlabel.lower()
    np.testing.assert_allclose(x_nm[0], 400.0)
    np.testing.assert_allclose(x_nm[63], cal.pixel_to_nm([63.0])[0])

    fig = intensity_figure(frame.intensity, calibration=cal)
    np.testing.assert_allclose(fig.data[0].x, x_nm)
    assert "nm" in str(fig.layout.xaxis.title.text).lower()

    state = TeachSpecUiState()
    load_preview_calibration(state, path)
    assert state.calibration is not None
    assert state.error == ""
    assert "educational" in state.status.lower()
    assert "auto-cal" in state.status.lower()


def test_build_ui_smoke_without_server() -> None:
    """Import/build TeachSpec UI without starting NiceGUI server."""
    pytest.importorskip("nicegui")
    from nicegui import ui

    assert hasattr(ui, "card")
    assert hasattr(ui, "plotly")
    assert hasattr(ui, "timer")
    assert not hasattr(ui, "banner")

    from teachspec.ui_app import _BANNER_TEXT, build_ui

    assert "educational" in _BANNER_TEXT.lower()
    assert "pixel" in _BANNER_TEXT.lower()
    assert "compound" in _BANNER_TEXT.lower()
    state = build_ui()
    assert state.mode == "mock"
    assert state.frame is not None
    assert state.streaming is False


def test_open_live_source_missing_opencv_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """Live open path surfaces install hint when OpenCV missing (no camera)."""
    import builtins
    import sys
    from typing import Any

    real_import = builtins.__import__

    def _guarded_import(name: str, *args: Any, **kwargs: Any):
        if name == "cv2" or name.startswith("cv2."):
            raise ImportError("No module named 'cv2'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _guarded_import)
    monkeypatch.delitem(sys.modules, "cv2", raising=False)

    from teachspec.ui_app import open_live_source

    with pytest.raises(ImportError, match=r"teachspec"):
        open_live_source(0)
