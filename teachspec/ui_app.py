"""TeachSpec live preview — minimal NiceGUI intensity-vs-pixel plot.

Requires: ``pip install -e ".[ui,teachspec]"``
(``[ui]`` for NiceGUI+Plotly; ``[teachspec]`` OpenCV only needed for Live mode)

Launch:
    python -m teachspec.ui_app
    # or: teachspec-ui

Default mode is Mock (camera-free). Live uses ``open_uvc_source``.
Educational only — intensity vs pixel until calibrated; no compound ID.
See ``docs/family/teachspec/SAFETY.md``.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from teachspec.mock_source import generate_mock_frame
from teachspec.optical import OpticalLiveFrame

try:
    import plotly.graph_objects as go
    from nicegui import ui
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        'NiceGUI/Plotly not installed. Run: pip install -e ".[ui]"\n'
        f"(Live camera also needs: pip install -e \".[teachspec]\")\n"
        f"Original error: {exc}"
    ) from exc

_STREAM_INTERVAL_S = 0.15  # ≈6.7 Hz (within 5–10 Hz target)
_PORT = 8082
_BANNER_TEXT = (
    "EDUCATIONAL — TeachSpec live preview. Intensity vs pixel index until you "
    "apply teachspec.calibration (no cal UI here). Not compound identification. "
    "Classroom use: docs/family/teachspec/SAFETY.md. Default Mock needs no camera."
)
_SAFETY_LINK = (
    "https://github.com/Garthnesss/chemspec-workbench/blob/main/"
    "docs/family/teachspec/SAFETY.md"
)


class TeachSpecUiState:
    """Minimal streaming state (mock by default; live optional)."""

    def __init__(self) -> None:
        self.mode: str = "mock"  # "mock" | "live"
        self.device_index: int = 0
        self.streaming: bool = False
        self.frame: OpticalLiveFrame | None = None
        self.frame_index: int = 0
        self.mock_seed: int = 42
        self.source: Any | None = None
        self.status: str = "Mock ready — Start stream (no camera)."
        self.error: str = ""

    def close_source(self) -> None:
        if self.source is not None:
            try:
                self.source.close()
            except Exception:  # noqa: BLE001
                pass
            self.source = None


def intensity_figure(
    intensity: np.ndarray | None,
    *,
    title: str = "Intensity vs pixel",
    source_label: str = "mock",
) -> go.Figure:
    """Build a Plotly line figure from 1-D intensity (testable without NiceGUI)."""
    fig = go.Figure()
    if intensity is None or len(intensity) == 0:
        fig.update_layout(
            title=title,
            xaxis_title="pixel",
            yaxis_title="intensity (a.u.)",
            template="plotly_white",
            height=420,
            annotations=[
                {
                    "text": "No frame yet — Start stream",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                }
            ],
        )
        return fig
    y = np.asarray(intensity, dtype=float)
    x = np.arange(y.size, dtype=float)
    fig.add_trace(
        go.Scatter(x=x, y=y, mode="lines", name=source_label, line={"width": 1.5})
    )
    fig.update_layout(
        title=title,
        xaxis_title="pixel",
        yaxis_title="intensity (a.u.)",
        template="plotly_white",
        height=420,
        margin={"l": 60, "r": 20, "t": 50, "b": 50},
        showlegend=True,
    )
    return fig


def read_mock_frame(*, seed: int | None = 42, n_pixels: int = 640) -> OpticalLiveFrame:
    """One synthetic teaching frame (camera-free)."""
    frame, _truth = generate_mock_frame(n_pixels=n_pixels, seed=seed)
    return frame


def open_live_source(device_index: int = 0) -> Any:
    """Open live UVC via teachspec factory (ImportError if OpenCV missing)."""
    from teachspec.uvc_ingest import open_uvc_source

    return open_uvc_source(device_index=int(device_index))


def stream_tick(state: TeachSpecUiState) -> OpticalLiveFrame:
    """Read one frame into state (mock or live). Raises on hardware/import errors."""
    if state.mode == "live":
        if state.source is None:
            state.source = open_live_source(state.device_index)
        frame = state.source.read_frame()
    else:
        # Mild seed walk so successive mock frames are visibly alive
        frame = read_mock_frame(seed=state.mock_seed + state.frame_index)
    state.frame = frame
    state.frame_index += 1
    kind = "live" if state.mode == "live" else "mock"
    state.status = (
        f"{kind} frame #{state.frame_index} — {len(frame.intensity)} pixels "
        "(intensity vs pixel; not calibrated)"
    )
    state.error = ""
    return frame


def build_ui() -> TeachSpecUiState:
    """Construct the single-page UI (no ``ui.run`` — safe for pytest smoke)."""
    state = TeachSpecUiState()
    # Prime one mock frame so the plot is not blank
    try:
        stream_tick(state)
    except Exception as exc:  # noqa: BLE001
        state.error = str(exc)

    ui.page_title("TeachSpec live preview")
    ui.markdown("# TeachSpec live preview").classes("text-h5")

    with ui.card().classes("w-full bg-amber-50"):
        ui.label(_BANNER_TEXT).classes("text-sm")
        ui.link("SAFETY.md (classroom)", _SAFETY_LINK, new_tab=True).classes("text-sm")

    status_label = ui.label(state.status).classes("text-caption")
    error_label = ui.label(state.error).classes("text-negative text-sm")
    plot = ui.plotly(
        intensity_figure(
            None if state.frame is None else state.frame.intensity,
            source_label=state.mode,
        )
    ).classes("w-full")

    def refresh() -> None:
        status_label.set_text(state.status)
        error_label.set_text(state.error or "")
        src = state.mode
        y = None if state.frame is None else state.frame.intensity
        title = (
            f"TeachSpec — {src} (intensity vs pixel)"
            if y is not None
            else "Intensity vs pixel"
        )
        plot.update_figure(intensity_figure(y, title=title, source_label=src))

    with ui.card().classes("w-full"):
        ui.label("Source").classes("text-h6")
        mode_toggle = ui.toggle(
            {"mock": "Mock", "live": "Live"},
            value="mock",
        ).props("outline")
        device_input = ui.number(
            label="UVC device index",
            value=0,
            min=0,
            step=1,
            format="%.0f",
        ).classes("w-40")

        def on_mode_change(_e: Any = None) -> None:
            new_mode = str(mode_toggle.value or "mock")
            if new_mode != state.mode:
                state.streaming = False
                state.close_source()
                state.mode = new_mode
                state.frame_index = 0
                state.status = (
                    "Live selected — Start stream (needs camera + [teachspec] extra)."
                    if new_mode == "live"
                    else "Mock selected — Start stream (no camera)."
                )
                state.error = ""
                refresh()

        mode_toggle.on_value_change(on_mode_change)

        def start_stream() -> None:
            state.device_index = int(device_input.value or 0)
            state.mode = str(mode_toggle.value or "mock")
            state.close_source()
            state.streaming = True
            state.error = ""
            state.status = f"Streaming ({state.mode})…"
            refresh()

        def stop_stream() -> None:
            state.streaming = False
            state.close_source()
            state.status = "Streaming stopped"
            refresh()

        with ui.row().classes("gap-2 items-center flex-wrap mt-2"):
            ui.button("Start", on_click=start_stream, color="positive")
            ui.button("Stop", on_click=stop_stream, color="negative")
            ui.label(f"≈ {_STREAM_INTERVAL_S:.2f}s / tick (~{1 / _STREAM_INTERVAL_S:.0f} Hz)").classes(
                "text-caption"
            )

        def on_timer() -> None:
            if not state.streaming:
                return
            try:
                stream_tick(state)
                refresh()
            except Exception as exc:  # noqa: BLE001
                state.streaming = False
                state.close_source()
                state.error = str(exc)
                state.status = "Stream stopped (error)"
                refresh()

        ui.timer(_STREAM_INTERVAL_S, on_timer)

    with ui.expansion("Honesty / non-goals", icon="info").classes("w-full"):
        ui.markdown(
            "- **Educational** preview only.\n"
            "- Plot is **intensity vs pixel** (no nm axis until calibration).\n"
            "- **No** compound identification.\n"
            "- **Mock** is the default (CI / machines without a camera).\n"
            "- **Live** needs `pip install -e \".[ui,teachspec]\"` + a UVC device.\n"
            "- See [`SAFETY.md`](" + _SAFETY_LINK + ")."
        )

    refresh()
    return state


def main() -> int:
    build_ui()
    ui.run(title="TeachSpec live preview", reload=False, show=False, port=_PORT)
    return 0


if __name__ in {"__main__", "__mp_main__"}:
    main()
