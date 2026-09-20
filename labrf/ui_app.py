"""LabRF Monitor — minimal NiceGUI UI (mock IQ by default).

Requires: ``pip install -e ".[ui]"``

Launch:
    python -m labrf.ui_app
    # or: python -m labrf
    # or: labrf-ui
"""

from __future__ import annotations

import numpy as np

from labrf.backend import MockIqSource
from labrf.fft_spectrum import iq_to_spectrum
from labrf.iq import DEFAULT_IQ_FIXTURE, ensure_default_fixture, load_iq_fixture
from labrf.presets import PRESETS_DISCLAIMER, load_presets
from labrf.waterfall import WaterfallBuffer
from spectrum_core import Peak, Spectrum, find_peaks

try:
    import plotly.graph_objects as go
    from nicegui import ui
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        'NiceGUI/Plotly not installed. Run: pip install -e ".[ui]"\n'
        f"Original error: {exc}"
    ) from exc

_N_FFT = 2048
_WATERFALL_DEPTH = 48


class LabRfState:
    def __init__(self) -> None:
        pack = load_presets()
        self.preset_pack = pack
        self.disclaimer = pack.disclaimer or PRESETS_DISCLAIMER
        self.center_hz = 98e6
        self.sample_rate = 2.048e6
        self.preset_id = "fm_broadcast"
        self.source = MockIqSource(
            sample_rate=self.sample_rate,
            center_freq=self.center_hz,
            seed=42,
        )
        self.spectrum: Spectrum | None = None
        self.peaks: list[Peak] = []
        self.waterfall = WaterfallBuffer(maxlen=_WATERFALL_DEPTH)
        self.prominence: float | None = None  # auto
        self.status = "Mock IQ ready — click Capture or Load mock fixture."
        self.error = ""


def _format_mhz(hz: float) -> str:
    return f"{hz / 1e6:.4f}"


def _apply_preset(state: LabRfState, preset_id: str) -> None:
    p = state.preset_pack.by_id(preset_id)
    state.preset_id = preset_id
    state.center_hz = p.center_hz
    state.sample_rate = p.sample_rate_hz
    state.source.configure(center_freq=state.center_hz, sample_rate=state.sample_rate)
    state.status = f"Preset: {p.name} @ {_format_mhz(p.center_hz)} MHz (educational)"
    state.error = ""


def _capture_mock(state: LabRfState) -> None:
    state.source.configure(center_freq=state.center_hz, sample_rate=state.sample_rate)
    iq = state.source.read_samples(_N_FFT)
    spec = iq_to_spectrum(
        iq,
        sample_rate=state.sample_rate,
        center_freq=state.center_hz,
        window="hann",
        x_unit="MHz",
        y_unit="dB",
        title=f"Mock RF @ {_format_mhz(state.center_hz)} MHz",
        meta={"source": "mock"},
    )
    state.spectrum = spec
    state.peaks = find_peaks(spec, prominence=state.prominence)
    state.waterfall.push(spec)
    state.status = (
        f"Captured mock spectrum ({len(spec)} bins, "
        f"{len(state.peaks)} peaks, waterfall={len(state.waterfall)})"
    )
    state.error = ""


def _load_fixture(state: LabRfState) -> None:
    ensure_default_fixture()
    iq, meta = load_iq_fixture(DEFAULT_IQ_FIXTURE)
    state.center_hz = float(meta["center_freq"])
    state.sample_rate = float(meta["sample_rate"])
    state.source = MockIqSource(fixture_path=str(DEFAULT_IQ_FIXTURE))
    # Use a contiguous block for FFT
    n = min(len(iq), _N_FFT)
    if n < _N_FFT:
        block = np.zeros(_N_FFT, dtype=np.complex128)
        block[:n] = iq[:n]
    else:
        block = iq[:_N_FFT]
    spec = iq_to_spectrum(
        block,
        sample_rate=state.sample_rate,
        center_freq=state.center_hz,
        window="hann",
        x_unit="MHz",
        y_unit="dB",
        title="Mock IQ fixture (synthetic)",
        meta={**meta, "source": "fixture"},
    )
    state.spectrum = spec
    state.peaks = find_peaks(spec, prominence=state.prominence)
    state.waterfall.clear()
    state.waterfall.push(spec)
    state.status = f"Loaded fixture {DEFAULT_IQ_FIXTURE.name} (synthetic)"
    state.error = ""


def _spectrum_figure(state: LabRfState) -> go.Figure:
    fig = go.Figure()
    if state.spectrum is None:
        fig.update_layout(
            title="RF power spectrum (no data yet)",
            xaxis_title="Frequency (MHz)",
            yaxis_title="Power (dB)",
            template="plotly_white",
            height=360,
        )
        return fig
    s = state.spectrum
    fig.add_trace(
        go.Scatter(x=s.x, y=s.y, mode="lines", name="Power", line=dict(width=1.5))
    )
    if state.peaks:
        fig.add_trace(
            go.Scatter(
                x=[p.x for p in state.peaks[:20]],
                y=[p.y for p in state.peaks[:20]],
                mode="markers+text",
                name="Peaks",
                marker=dict(size=8, symbol="triangle-down", color="#d62728"),
                text=[f"{p.x:.3f}" for p in state.peaks[:8]],
                textposition="top center",
            )
        )
    fig.update_layout(
        title=s.title or "RF power spectrum",
        xaxis_title=f"Frequency ({s.x_unit})",
        yaxis_title=f"Power ({s.y_unit})",
        template="plotly_white",
        height=360,
        margin=dict(l=50, r=20, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def _waterfall_figure(state: LabRfState) -> go.Figure:
    fig = go.Figure()
    x, z = state.waterfall.as_matrix()
    if z.size == 0:
        fig.update_layout(
            title="Waterfall (empty)",
            xaxis_title="Frequency (MHz)",
            yaxis_title="Frame (oldest → newest)",
            template="plotly_white",
            height=280,
        )
        return fig
    fig.add_trace(
        go.Heatmap(
            x=x,
            z=z,
            colorscale="Viridis",
            colorbar=dict(title="dB"),
        )
    )
    fig.update_layout(
        title=f"Waterfall ({z.shape[0]} frames)",
        xaxis_title="Frequency (MHz)",
        yaxis_title="Frame index (oldest → newest)",
        template="plotly_white",
        height=280,
        margin=dict(l=50, r=20, t=40, b=40),
    )
    return fig


def build_ui() -> None:
    state = LabRfState()
    _apply_preset(state, state.preset_id)

    ui.page_title("LabRF Monitor")
    with ui.header().classes("items-center justify-between"):
        ui.label("LabRF Monitor").classes("text-h5")
        ui.label("receive-only · mock IQ · educational").classes("text-caption")

    with ui.banner(result=None).classes("bg-amber-100 text-amber-900").props(
        "rounded"
    ) as banner:
        with ui.row().classes("items-center w-full"):
            ui.icon("warning", color="orange")
            ui.label(state.disclaimer).classes("text-sm")
            ui.space()
            ui.button(icon="close", on_click=banner.delete).props("flat dense")

    status_label = ui.label(state.status).classes("text-body2")
    error_label = ui.label("").classes("text-negative text-sm")

    spectrum_plot = ui.plotly(_spectrum_figure(state)).classes("w-full")
    waterfall_plot = ui.plotly(_waterfall_figure(state)).classes("w-full")

    peak_table = ui.table(
        columns=[
            {"name": "x", "label": "Freq (MHz)", "field": "x"},
            {"name": "y", "label": "Power (dB)", "field": "y"},
            {"name": "prominence", "label": "Prominence", "field": "prominence"},
        ],
        rows=[],
        row_key="x",
    ).classes("w-full")

    def refresh() -> None:
        status_label.set_text(state.status)
        error_label.set_text(state.error)
        spectrum_plot.update_figure(_spectrum_figure(state))
        waterfall_plot.update_figure(_waterfall_figure(state))
        peak_table.rows = [
            {
                "x": round(p.x, 4),
                "y": round(p.y, 2),
                "prominence": round(p.prominence, 3),
            }
            for p in state.peaks[:30]
        ]
        peak_table.update()

    with ui.card().classes("w-full"):
        ui.label("Tuning").classes("text-h6")
        with ui.row().classes("w-full items-end flex-wrap gap-4"):
            preset_select = ui.select(
                options={p.id: p.name for p in state.preset_pack.presets},
                value=state.preset_id,
                label="Educational preset",
            ).classes("min-w-64")

            center_input = ui.number(
                label="Center (MHz)",
                value=state.center_hz / 1e6,
                format="%.4f",
                step=0.1,
            ).classes("w-40")

            rate_input = ui.number(
                label="Sample rate / span (Hz)",
                value=state.sample_rate,
                format="%.0f",
                step=1000,
            ).classes("w-48")

        def on_preset() -> None:
            try:
                _apply_preset(state, str(preset_select.value))
                center_input.value = state.center_hz / 1e6
                rate_input.value = state.sample_rate
                refresh()
            except Exception as exc:  # noqa: BLE001
                state.error = str(exc)
                refresh()

        def sync_tune_from_inputs() -> None:
            state.center_hz = float(center_input.value) * 1e6
            state.sample_rate = float(rate_input.value)
            state.source.configure(
                center_freq=state.center_hz, sample_rate=state.sample_rate
            )

        with ui.row().classes("gap-2 flex-wrap"):
            ui.button("Apply preset", on_click=on_preset, color="primary")
            ui.button(
                "Capture mock spectrum",
                on_click=lambda: (
                    sync_tune_from_inputs(),
                    _capture_mock(state),
                    refresh(),
                ),
            )
            ui.button(
                "Load mock fixture",
                on_click=lambda: (_load_fixture(state), refresh()),
            )
            ui.button(
                "Clear waterfall",
                on_click=lambda: (
                    state.waterfall.clear(),
                    setattr(state, "status", "Waterfall cleared"),
                    refresh(),
                ),
            ).props("outline")

    with ui.expansion("Peak table", icon="table_chart").classes("w-full"):
        peak_table

    with ui.expansion("Honesty / non-goals", icon="info").classes("w-full"):
        ui.markdown(
            "- **Receive-only** — no transmit path.\n"
            "- **No chemical identification** via RF.\n"
            "- **No demodulation / compliance claims** in Phase 1.\n"
            "- Presets are **educational**, not regulatory advice.\n"
            "- Live RTL-SDR needs `pip install -e \".[labrf]\"` + hardware "
            "(not required for this mock UI)."
        )

    # Initial capture so the UI is not blank
    try:
        _capture_mock(state)
    except Exception as exc:  # noqa: BLE001
        state.error = str(exc)
    refresh()


def main() -> int:
    build_ui()
    ui.run(title="LabRF Monitor", reload=False, show=False, port=8081)
    return 0


if __name__ in {"__main__", "__mp_main__"}:
    main()
