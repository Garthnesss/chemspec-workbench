"""LabRF Monitor — NiceGUI UI with streaming mock waterfall (no dongle).

Requires: ``pip install -e ".[ui]"``

Launch:
    python -m labrf.ui_app
    # or: python -m labrf
    # or: labrf-ui
"""

from __future__ import annotations

import numpy as np

from labrf.backend import MockIqSource
from labrf.events import ThresholdEventLog
from labrf.fft_spectrum import iq_to_spectrum
from labrf.iq import DEFAULT_IQ_FIXTURE, ensure_default_fixture, load_iq_fixture
from labrf.presets import PRESETS_DISCLAIMER, load_presets
from labrf.stream import MockStreamGenerator, format_labrf_provenance
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
_STREAM_INTERVAL_S = 0.25
_BANNER_TEXT = (
    "DEMO / EDUCATIONAL — LabRF Monitor is receive-only situational awareness. "
    "Default mode uses synthetic mock IQ (no dongle). "
    "Presets are teaching aids, not regulatory advice. "
    "No chemical identification, no demodulation, no transmit, no compliance claims."
)


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
        self.source_kind = "mock"
        self.streaming = False
        self.stream = MockStreamGenerator(source=self.source, n_fft=_N_FFT)
        self.event_log = ThresholdEventLog(threshold_db=-10.0)
        self.status = "Mock IQ ready — Start stream, Capture, or Load mock fixture."
        self.error = ""

    def provenance(self) -> str:
        return format_labrf_provenance(
            source_kind=self.source_kind,
            center_hz=self.center_hz,
            sample_rate=self.sample_rate,
            frames=len(self.waterfall),
            streaming=self.streaming,
            peak_count=len(self.peaks),
            threshold_db=self.event_log.threshold_db,
            event_count=len(self.event_log),
        )


def _format_mhz(hz: float) -> str:
    return f"{hz / 1e6:.4f}"


def _rebuild_stream(state: LabRfState) -> None:
    state.stream = MockStreamGenerator(
        source=state.source,
        n_fft=_N_FFT,
        frame_index=state.stream.frame_index if state.stream else 0,
    )
    state.source_kind = state.stream.source_kind


def _apply_preset(state: LabRfState, preset_id: str) -> None:
    p = state.preset_pack.by_id(preset_id)
    state.preset_id = preset_id
    state.center_hz = p.center_hz
    state.sample_rate = p.sample_rate_hz
    state.source.configure(center_freq=state.center_hz, sample_rate=state.sample_rate)
    _rebuild_stream(state)
    state.status = f"Preset: {p.name} @ {_format_mhz(p.center_hz)} MHz (educational)"
    state.error = ""


def _ingest_spectrum(state: LabRfState, spec: Spectrum) -> None:
    state.spectrum = spec
    state.peaks = find_peaks(spec, prominence=state.prominence)
    state.waterfall.push(spec)
    state.event_log.check(spec, state.peaks)


def _capture_mock(state: LabRfState) -> None:
    state.source.configure(center_freq=state.center_hz, sample_rate=state.sample_rate)
    _rebuild_stream(state)
    frame = state.stream.next_frame()
    _ingest_spectrum(state, frame.spectrum)
    state.status = (
        f"Captured mock spectrum ({len(frame.spectrum)} bins, "
        f"{len(state.peaks)} peaks, waterfall={len(state.waterfall)})"
    )
    state.error = ""


def _stream_tick(state: LabRfState) -> None:
    """One streaming step — called by NiceGUI timer (no sleep here)."""
    if not state.streaming:
        return
    state.source.configure(center_freq=state.center_hz, sample_rate=state.sample_rate)
    frame = state.stream.next_frame()
    state.source_kind = frame.source_kind
    _ingest_spectrum(state, frame.spectrum)
    state.status = (
        f"Streaming mock IQ — frame {frame.frame_index} "
        f"(waterfall={len(state.waterfall)}, events={len(state.event_log)})"
    )
    state.error = ""


def _load_fixture(state: LabRfState) -> None:
    ensure_default_fixture()
    iq, meta = load_iq_fixture(DEFAULT_IQ_FIXTURE)
    state.center_hz = float(meta["center_freq"])
    state.sample_rate = float(meta["sample_rate"])
    state.source = MockIqSource(fixture_path=str(DEFAULT_IQ_FIXTURE))
    _rebuild_stream(state)
    state.source_kind = "fixture"
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
    state.waterfall.clear()
    _ingest_spectrum(state, spec)
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
    thr = state.event_log.threshold_db
    fig.add_hline(
        y=thr,
        line_dash="dash",
        line_color="#e67e22",
        annotation_text=f"threshold {thr:.1f} dB",
        annotation_position="top left",
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
        title=f"Waterfall ({z.shape[0]} frames)"
        + (" · streaming" if state.streaming else ""),
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

    with ui.card().classes("w-full bg-amber-200 text-amber-950 q-pa-sm") as banner:
        with ui.row().classes("items-center w-full gap-2 no-wrap"):
            ui.icon("warning", color="orange").classes("text-2xl")
            with ui.column().classes("gap-0"):
                ui.label(_BANNER_TEXT).classes("text-sm font-medium")
                ui.label(state.disclaimer).classes("text-xs opacity-80")
            ui.space()
            ui.button(icon="close", on_click=banner.delete).props("flat dense")

    status_label = ui.label(state.status).classes("text-body2")
    provenance_label = ui.label(state.provenance()).classes(
        "text-caption text-grey-8 font-mono"
    )
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

    event_table = ui.table(
        columns=[
            {"name": "timestamp", "label": "UTC time", "field": "timestamp"},
            {"name": "freq", "label": "Freq (MHz)", "field": "freq"},
            {"name": "level", "label": "Level (dB)", "field": "level"},
            {"name": "kind", "label": "Kind", "field": "kind"},
        ],
        rows=[],
        row_key="timestamp",
    ).classes("w-full")

    def refresh() -> None:
        status_label.set_text(state.status)
        provenance_label.set_text(state.provenance())
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
        event_table.rows = list(reversed(state.event_log.rows()[-50:]))
        event_table.update()

    # --- Tuning card ---
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

        ui.label("Quick presets (jump center / span)").classes("text-caption mt-2")
        with ui.row().classes("gap-2 flex-wrap"):
            for p in state.preset_pack.presets:

                def _make_jump(pid: str = p.id):
                    def _jump() -> None:
                        try:
                            was = state.streaming
                            if was:
                                state.streaming = False
                            _apply_preset(state, pid)
                            preset_select.value = pid
                            center_input.value = state.center_hz / 1e6
                            rate_input.value = state.sample_rate
                            state.waterfall.clear()
                            _capture_mock(state)
                            if was:
                                state.streaming = True
                            refresh()
                        except Exception as exc:  # noqa: BLE001
                            state.error = str(exc)
                            refresh()

                    return _jump

                short = p.name.split("(")[0].strip()
                ui.button(short, on_click=_make_jump()).props("outline dense")

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
            _rebuild_stream(state)

        with ui.row().classes("gap-2 flex-wrap mt-2"):
            ui.button("Apply preset", on_click=on_preset, color="primary")
            ui.button(
                "Load mock fixture",
                on_click=lambda: (
                    setattr(state, "streaming", False),
                    _load_fixture(state),
                    center_input.set_value(state.center_hz / 1e6),
                    rate_input.set_value(state.sample_rate),
                    refresh(),
                ),
                color="secondary",
            )
            ui.button(
                "Capture once",
                on_click=lambda: (
                    sync_tune_from_inputs(),
                    _capture_mock(state),
                    refresh(),
                ),
            )
            ui.button(
                "Clear waterfall",
                on_click=lambda: (
                    state.waterfall.clear(),
                    setattr(state, "status", "Waterfall cleared"),
                    refresh(),
                ),
            ).props("outline")

    # --- Streaming card ---
    with ui.card().classes("w-full"):
        ui.label("Streaming mock waterfall").classes("text-h6")
        ui.label(
            "Timer pulls successive synthetic IQ frames (noise/tone jitter). "
            "No dongle required."
        ).classes("text-caption")
        stream_btn_row = ui.row().classes("gap-2 items-center")

        def start_stream() -> None:
            sync_tune_from_inputs()
            state.streaming = True
            state.status = "Streaming started (mock IQ)"
            refresh()

        def stop_stream() -> None:
            state.streaming = False
            state.status = "Streaming stopped"
            refresh()

        with stream_btn_row:
            ui.button("Start stream", on_click=start_stream, color="positive")
            ui.button("Stop stream", on_click=stop_stream, color="negative")
            ui.label(f"Interval ≈ {_STREAM_INTERVAL_S:.2f}s").classes("text-caption")

        def on_timer() -> None:
            if not state.streaming:
                return
            try:
                _stream_tick(state)
                refresh()
            except Exception as exc:  # noqa: BLE001
                state.streaming = False
                state.error = str(exc)
                refresh()

        ui.timer(_STREAM_INTERVAL_S, on_timer)

    # --- Threshold card ---
    with ui.card().classes("w-full"):
        ui.label("Threshold event log").classes("text-h6")
        ui.label(
            "When peak or max bin exceeds the power threshold, a timestamped "
            "event is recorded (freq + level)."
        ).classes("text-caption")
        with ui.row().classes("items-end gap-4 flex-wrap"):
            thr_input = ui.number(
                label="Power threshold (dB)",
                value=state.event_log.threshold_db,
                format="%.1f",
                step=1.0,
            ).classes("w-48")

            def apply_threshold() -> None:
                state.event_log.set_threshold(float(thr_input.value))
                state.status = f"Threshold set to {state.event_log.threshold_db:.1f} dB"
                if state.spectrum is not None:
                    # Re-check current frame so demos see immediate feedback
                    state.event_log.check(state.spectrum, state.peaks)
                refresh()

            ui.button("Apply threshold", on_click=apply_threshold)
            ui.button(
                "Clear events",
                on_click=lambda: (
                    state.event_log.clear(),
                    setattr(state, "status", "Event log cleared"),
                    refresh(),
                ),
            ).props("outline")

            def export_events() -> None:
                csv_text = state.event_log.to_csv()
                ui.download(csv_text.encode("utf-8"), "labrf_threshold_events.csv")

            ui.button("Export events CSV", on_click=export_events).props("outline")

        event_table

    with ui.expansion("Peak table", icon="table_chart").classes("w-full"):
        peak_table

    with ui.expansion("Honesty / non-goals", icon="info").classes("w-full"):
        ui.markdown(
            "- **Receive-only** — no transmit path.\n"
            "- **No chemical identification** via RF.\n"
            "- **No demodulation / compliance claims** in Phase 1.\n"
            "- Presets are **educational**, not regulatory advice.\n"
            "- Streaming uses **synthetic mock IQ** by default "
            "(fixture / RTL optional).\n"
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
