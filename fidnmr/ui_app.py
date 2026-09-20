"""FID/NMR playground UI — mock FID time + spectrum views.

Requires: ``pip install -e ".[ui]"``

Launch:
    python -m fidnmr.ui_app
    # or: fidnmr-ui

Educational / synthetic only — no magnet, no compound ID / structure elucidation.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from spectrum_core import find_peaks
from spectrum_core.spectrum import Spectrum

from fidnmr.mock_source import DEFAULT_TEACHING_PEAKS_PPM, generate_mock_fid
from fidnmr.process import fid_to_spectrum

try:
    import plotly.graph_objects as go
    from nicegui import ui
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        'NiceGUI/Plotly not installed. Run: pip install -e ".[ui]"\n'
        f"Original error: {exc}"
    ) from exc

_PORT = 8083
_BANNER_TEXT = (
    "EDUCATIONAL — FID/NMR playground. Synthetic 1H-like mock FID only. "
    "No magnet, no live spectrometer driver, not compound identification "
    "or structure elucidation. Teaching ppm axis uses declared obs_mhz + ref_ppm."
)


class FidNmrUiState:
    """Headless-testable processing state for the mock playground."""

    def __init__(self) -> None:
        self.npts: int = 2048
        self.lb_hz: float = 1.0
        self.phc0_deg: float = 0.0
        self.phc1_deg: float = 0.0
        self.x_unit: str = "ppm"  # "ppm" | "Hz"
        self.seed: int = 42
        self.fid: Any = None
        self.spectrum: Spectrum | None = None
        self.peaks: list = []
        self.status: str = "Mock FID ready — adjust phase / line-broadening."
        self.error: str = ""
        self.regenerate()

    def regenerate(self) -> None:
        """New synthetic FID + spectrum from current processing knobs."""
        self.error = ""
        self.fid, _truth = generate_mock_fid(npts=self.npts, seed=self.seed)
        self.rebuild_spectrum()

    def rebuild_spectrum(self) -> None:
        if self.fid is None:
            self.spectrum = None
            self.peaks = []
            return
        spec = fid_to_spectrum(
            self.fid,
            lb_hz=float(self.lb_hz),
            phc0_deg=float(self.phc0_deg),
            phc1_deg=float(self.phc1_deg),
            x_unit=self.x_unit,  # type: ignore[arg-type]
            title="synthetic 1H-like mock (not a real acquisition)",
        )
        self.spectrum = spec
        pick = Spectrum(
            x=spec.x,
            y=np.abs(spec.y),
            x_unit=spec.x_unit,
            y_unit=spec.y_unit,
            title=spec.title,
            meta=dict(spec.meta),
        )
        prominence = float(np.max(np.abs(spec.y))) * 0.05
        if prominence <= 0:
            self.peaks = []
        else:
            self.peaks = find_peaks(pick, prominence=prominence)
        self.status = (
            f"Mock {self.fid.nucleus} FID — {self.fid.npts} pts, "
            f"sw={self.fid.sw_hz:g} Hz, obs={self.fid.obs_mhz:g} MHz, "
            f"lb={self.lb_hz:g} Hz, phc0={self.phc0_deg:g}°, phc1={self.phc1_deg:g}°, "
            f"peaks={len(self.peaks)} on |y| ({self.x_unit})"
        )


def fid_time_figure(state: FidNmrUiState) -> go.Figure:
    """Plotly real/imag FID vs time (testable without NiceGUI server)."""
    fig = go.Figure()
    if state.fid is None:
        fig.update_layout(title="FID (no data)", template="plotly_white", height=320)
        return fig
    t = state.fid.time_axis_s()
    z = state.fid.signal
    fig.add_trace(
        go.Scatter(x=t, y=np.real(z), mode="lines", name="real", line={"width": 1.2})
    )
    fig.add_trace(
        go.Scatter(x=t, y=np.imag(z), mode="lines", name="imag", line={"width": 1.0})
    )
    fig.update_layout(
        title="FID time domain (synthetic)",
        xaxis_title="time (s)",
        yaxis_title="intensity (a.u.)",
        template="plotly_white",
        height=320,
        margin={"l": 60, "r": 20, "t": 40, "b": 40},
        showlegend=True,
    )
    return fig


def spectrum_figure(state: FidNmrUiState) -> go.Figure:
    """Plotly real spectrum + peak markers (testable without NiceGUI server)."""
    fig = go.Figure()
    spec = state.spectrum
    if spec is None:
        fig.update_layout(title="Spectrum (no data)", template="plotly_white", height=360)
        return fig
    fig.add_trace(
        go.Scatter(
            x=spec.x,
            y=spec.y,
            mode="lines",
            name="real FFT",
            line={"width": 1.4},
        )
    )
    if state.peaks:
        fig.add_trace(
            go.Scatter(
                x=[p.x for p in state.peaks],
                y=[float(np.interp(p.x, spec.x, spec.y)) for p in state.peaks],
                mode="markers",
                name="peaks on |y|",
                marker={"size": 8, "symbol": "x"},
            )
        )
    xlabel = "δ (ppm, teaching axis)" if spec.x_unit == "ppm" else "frequency (Hz)"
    if spec.x_unit == "ppm":
        fig.update_xaxes(autorange="reversed")
    fig.update_layout(
        title="Spectrum (synthetic mock — not compound ID)",
        xaxis_title=xlabel,
        yaxis_title="intensity (real part)",
        template="plotly_white",
        height=360,
        margin={"l": 60, "r": 20, "t": 40, "b": 40},
        showlegend=True,
    )
    return fig


def build_ui() -> FidNmrUiState:
    """Construct the single-page UI (no ``ui.run`` — safe for pytest smoke)."""
    state = FidNmrUiState()

    ui.page_title("FID/NMR playground")
    ui.markdown("# FID/NMR playground").classes("text-h5")

    with ui.card().classes("w-full bg-amber-50"):
        ui.label(_BANNER_TEXT).classes("text-sm")

    status_label = ui.label(state.status).classes("text-caption")
    error_label = ui.label(state.error).classes("text-negative text-sm")
    fid_plot = ui.plotly(fid_time_figure(state)).classes("w-full")
    spec_plot = ui.plotly(spectrum_figure(state)).classes("w-full")

    def refresh() -> None:
        status_label.set_text(state.status)
        error_label.set_text(state.error or "")
        fid_plot.update_figure(fid_time_figure(state))
        spec_plot.update_figure(spectrum_figure(state))

    with ui.card().classes("w-full"):
        ui.label("Processing (mock FID)").classes("text-h6")
        unit_toggle = ui.toggle({"ppm": "ppm", "Hz": "Hz"}, value="ppm").props("outline")
        lb = ui.number(label="lb_hz", value=state.lb_hz, min=0, step=0.5).classes("w-32")
        ph0 = ui.number(label="phc0 °", value=state.phc0_deg, step=5).classes("w-32")
        ph1 = ui.number(label="phc1 °", value=state.phc1_deg, step=5).classes("w-32")

        def apply_knobs() -> None:
            state.lb_hz = float(lb.value or 0.0)
            state.phc0_deg = float(ph0.value or 0.0)
            state.phc1_deg = float(ph1.value or 0.0)
            state.x_unit = str(unit_toggle.value or "ppm")
            if state.x_unit not in ("ppm", "Hz"):
                state.x_unit = "ppm"
            try:
                state.rebuild_spectrum()
            except Exception as exc:  # noqa: BLE001
                state.error = str(exc)
            refresh()

        unit_toggle.on_value_change(lambda _e: apply_knobs())
        lb.on("change", lambda _e: apply_knobs())
        ph0.on("change", lambda _e: apply_knobs())
        ph1.on("change", lambda _e: apply_knobs())

        def on_regen() -> None:
            state.seed = int(state.seed) + 1
            state.lb_hz = float(lb.value or 0.0)
            state.phc0_deg = float(ph0.value or 0.0)
            state.phc1_deg = float(ph1.value or 0.0)
            state.x_unit = str(unit_toggle.value or "ppm")
            state.regenerate()
            refresh()

        with ui.row().classes("gap-2 items-center flex-wrap mt-2"):
            ui.button("Apply", on_click=apply_knobs, color="primary")
            ui.button("New mock FID", on_click=on_regen)
            ui.label(
                "Teaching peaks (ppm, not a sample): "
                + ", ".join(f"{p:.1f}" for p in DEFAULT_TEACHING_PEAKS_PPM)
            ).classes("text-caption")

    with ui.expansion("Honesty / non-goals", icon="info").classes("w-full"):
        ui.markdown(
            "- **Synthetic mock only** — no magnet, no Bruker/Varian driver.\n"
            "- **No** compound identification or structure elucidation.\n"
            "- ppm axis is a teaching conversion (`ref_ppm + f_Hz / obs_MHz`).\n"
            "- Peak marks use prominence on **|y|** so phase sign does not hide lines.\n"
            "- Licensed public FID fixtures remain Planned."
        )

    refresh()
    return state


def main() -> int:
    build_ui()
    ui.run(title="FID/NMR playground", reload=False, show=False, port=_PORT)
    return 0


if __name__ in {"__main__", "__mp_main__"}:
    main()
