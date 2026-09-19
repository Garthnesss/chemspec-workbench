"""ChemSpec Workbench — interactive MVP UI (NiceGUI + Plotly).

Requires optional deps: ``pip install -e ".[ui]"``

Launch:
    python -m chemspec.ui_app
    # or: chemspec-ui
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from spectrum_core import (
    Peak,
    Spectrum,
    baseline_polynomial,
    find_peaks,
    ingest_csv,
    overlay,
)

from chemspec.ui_helpers import (
    FIXTURE_PRESETS,
    axis_label,
    guess_column_mapping,
    sniff_csv_header,
)

try:
    import plotly.graph_objects as go
    from nicegui import ui
except ImportError as exc:  # pragma: no cover - exercised only without [ui]
    raise SystemExit(
        'NiceGUI/Plotly not installed. Run: pip install -e ".[ui]"\n'
        f"Original error: {exc}"
    ) from exc


class WorkbenchState:
    """Mutable session state for the local MVP UI."""

    def __init__(self) -> None:
        self.primary: Spectrum | None = None
        self.overlay_spec: Spectrum | None = None
        self.primary_path: str = ""
        self.overlay_path: str = ""
        self.headers: list[str] = []
        self.x_col: int | str = 0
        self.y_col: int | str = 1
        self.x_unit: str = "nm"
        self.y_unit: str = "intensity"
        self.prominence: float = 0.15
        self.use_auto_prominence: bool = False
        self.baseline_on: bool = False
        self.baseline_degree: int = 1
        self.peaks: list[Peak] = []
        self.status: str = "Load a CSV or pick a synthetic fixture to begin."
        self.error: str = ""


def _working_spectrum(state: WorkbenchState, spec: Spectrum | None) -> Spectrum | None:
    if spec is None:
        return None
    if state.baseline_on:
        return baseline_polynomial(spec, degree=state.baseline_degree)
    return spec


def _prominence_arg(state: WorkbenchState) -> float | None:
    if state.use_auto_prominence:
        return None
    return float(state.prominence)


def _recompute_peaks(state: WorkbenchState) -> None:
    work = _working_spectrum(state, state.primary)
    if work is None:
        state.peaks = []
        return
    state.peaks = find_peaks(work, prominence=_prominence_arg(state))


def _load_from_path(
    state: WorkbenchState,
    path: Path | str,
    *,
    as_overlay: bool = False,
    x_col: int | str | None = None,
    y_col: int | str | None = None,
    x_unit: str | None = None,
    y_unit: str | None = None,
    title: str | None = None,
) -> None:
    path = Path(path)
    state.error = ""
    if not path.is_file():
        state.error = f"File not found: {path}"
        return

    headers = sniff_csv_header(path)
    guess = guess_column_mapping(headers)

    if not as_overlay:
        state.headers = headers
        state.x_col = x_col if x_col is not None else guess["x_col"]
        state.y_col = y_col if y_col is not None else guess["y_col"]
        state.x_unit = x_unit if x_unit is not None else guess["x_unit"]
        state.y_unit = y_unit if y_unit is not None else guess["y_unit"]
        xc, yc = state.x_col, state.y_col
        xu, yu = state.x_unit, state.y_unit
    else:
        xc = x_col if x_col is not None else guess["x_col"]
        yc = y_col if y_col is not None else guess["y_col"]
        xu = x_unit if x_unit is not None else guess["x_unit"]
        yu = y_unit if y_unit is not None else guess["y_unit"]

    try:
        spec = ingest_csv(
            path,
            x_col=xc,
            y_col=yc,
            x_unit=xu,  # type: ignore[arg-type]
            y_unit=yu,  # type: ignore[arg-type]
            title=title,
        )
    except Exception as exc:  # noqa: BLE001 — surface to UI
        state.error = f"Ingest failed: {exc}"
        return

    if as_overlay:
        if state.primary is not None and spec.x_unit != state.primary.x_unit:
            state.error = (
                f"Overlay x_unit={spec.x_unit!r} does not match "
                f"primary x_unit={state.primary.x_unit!r}"
            )
            return
        state.overlay_spec = spec
        state.overlay_path = str(path)
        state.status = f"Overlay loaded: {path.name} ({len(spec)} pts)"
    else:
        state.primary = spec
        state.primary_path = str(path)
        state.overlay_spec = None
        state.overlay_path = ""
        _recompute_peaks(state)
        state.status = (
            f"Loaded {path.name} — {len(spec)} pts, "
            f"x={spec.x_unit}, y={spec.y_unit}, peaks={len(state.peaks)}"
        )


def _load_fixture(
    state: WorkbenchState, key: str, *, as_overlay: bool = False
) -> None:
    cfg = FIXTURE_PRESETS[key]
    _load_from_path(
        state,
        cfg["path"],
        as_overlay=as_overlay,
        x_col=cfg["x_col"],
        y_col=cfg["y_col"],
        x_unit=cfg["x_unit"],
        y_unit=cfg["y_unit"],
        title=cfg["path"].stem,
    )
    if not as_overlay and not state.error:
        state.prominence = float(cfg["prominence"])
        state.baseline_degree = int(cfg["baseline_degree"])
        _recompute_peaks(state)
        state.status += f" (fixture: {cfg['label']})"


def _build_figure(state: WorkbenchState) -> go.Figure:
    fig = go.Figure()
    work = _working_spectrum(state, state.primary)
    if work is None:
        fig.update_layout(
            title="ChemSpec Workbench — load a spectrum",
            template="plotly_white",
            height=480,
            annotations=[
                dict(
                    text="No spectrum loaded",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=16, color="#888"),
                )
            ],
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig

    xlabel, ylabel = axis_label(work.x_unit, work.y_unit)
    label = work.title or "primary"
    if state.baseline_on:
        label += " (baseline on)"
    fig.add_trace(
        go.Scatter(
            x=work.x.tolist(),
            y=work.y.tolist(),
            mode="lines",
            name=label,
            line=dict(width=1.6, color="#1f77b4"),
        )
    )

    if state.peaks:
        fig.add_trace(
            go.Scatter(
                x=[p.x for p in state.peaks],
                y=[p.y for p in state.peaks],
                mode="markers+text",
                name=f"peaks (n={len(state.peaks)})",
                marker=dict(color="#d62728", size=9, symbol="circle"),
                text=[f"{p.x:.1f}" for p in state.peaks[:12]],
                textposition="top center",
                textfont=dict(size=10),
                cliponaxis=False,
            )
        )

    if state.overlay_spec is not None:
        try:
            pair = overlay([work, state.overlay_spec])
            ov = pair[1]
            fig.add_trace(
                go.Scatter(
                    x=ov.x.tolist(),
                    y=ov.y.tolist(),
                    mode="lines",
                    name=ov.title or "overlay",
                    line=dict(width=1.4, color="#ff7f0e", dash="dash"),
                )
            )
        except ValueError as exc:
            state.error = str(exc)

    fig.update_layout(
        title=f"ChemSpec — {work.title} (zoom/pan enabled)",
        xaxis_title=xlabel,
        yaxis_title=ylabel,
        template="plotly_white",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=60, r=20, t=60, b=60),
        dragmode="zoom",
    )
    if work.x_unit == "cm-1":
        fig.update_xaxes(autorange="reversed")
    fig.add_annotation(
        text="Synthetic fixtures are not real compounds — no ID claims.",
        xref="paper",
        yref="paper",
        x=0,
        y=-0.16,
        showarrow=False,
        font=dict(size=11, color="#666"),
        xanchor="left",
    )
    return fig


def _peak_rows(state: WorkbenchState) -> list[dict[str, Any]]:
    return [
        {
            "index": p.index,
            "x": round(p.x, 4),
            "y": round(p.y, 6),
            "prominence": round(p.prominence, 6),
        }
        for p in state.peaks
    ]


def _parse_col(raw: str) -> int | str:
    raw = raw.strip()
    if raw.isdigit() or (raw.startswith("-") and raw[1:].isdigit()):
        return int(raw)
    return raw


def create_app() -> WorkbenchState:
    """Build the NiceGUI page. Returns the session state object."""
    state = WorkbenchState()

    ui.colors(primary="#1f4e79")

    with ui.header().classes("items-center justify-between"):
        ui.label("ChemSpec Workbench").classes("text-h5")
        ui.label("MVP · spectrum_core · synthetic-safe").classes("text-caption")

    status_label = ui.label(state.status).classes("text-body2 q-px-md q-pt-sm")
    error_label = ui.label("").classes("text-negative q-px-md")

    # Forward-declare refresh via closure box
    widgets: dict[str, Any] = {}

    def refresh_ui() -> None:
        status_label.set_text(state.status)
        error_label.set_text(state.error or "")
        widgets["plot"].update_figure(_build_figure(state))
        table = widgets["peak_table"]
        table.rows = _peak_rows(state)
        table.update()
        widgets["path_input"].value = state.primary_path or widgets["path_input"].value
        widgets["x_col_input"].value = str(state.x_col)
        widgets["y_col_input"].value = str(state.y_col)
        widgets["x_unit_select"].value = state.x_unit
        widgets["y_unit_select"].value = state.y_unit
        widgets["prom_slider"].value = state.prominence
        widgets["baseline_toggle"].value = state.baseline_on
        widgets["degree_input"].value = state.baseline_degree
        if state.overlay_path:
            widgets["overlay_path_input"].value = state.overlay_path

    def on_load_path() -> None:
        state.x_col = _parse_col(str(widgets["x_col_input"].value or "0"))
        state.y_col = _parse_col(str(widgets["y_col_input"].value or "1"))
        state.x_unit = str(widgets["x_unit_select"].value)
        state.y_unit = str(widgets["y_unit_select"].value)
        _load_from_path(
            state,
            str(widgets["path_input"].value).strip(),
            x_col=state.x_col,
            y_col=state.y_col,
            x_unit=state.x_unit,
            y_unit=state.y_unit,
        )
        refresh_ui()

    def on_sniff() -> None:
        p = Path(str(widgets["path_input"].value).strip())
        if not p.is_file():
            state.error = f"File not found: {p}"
            refresh_ui()
            return
        headers = sniff_csv_header(p)
        guess = guess_column_mapping(headers)
        state.headers = headers
        state.x_col = guess["x_col"]
        state.y_col = guess["y_col"]
        state.x_unit = guess["x_unit"]
        state.y_unit = guess["y_unit"]
        state.status = (
            f"Detected columns {headers or '(numeric, use indices)'} → "
            f"x={state.x_col!r}, y={state.y_col!r}, "
            f"units {state.x_unit}/{state.y_unit}"
        )
        state.error = ""
        refresh_ui()

    def on_fixture(key: str) -> None:
        _load_fixture(state, key, as_overlay=False)
        refresh_ui()

    def on_params_change() -> None:
        state.prominence = float(widgets["prom_slider"].value)
        state.use_auto_prominence = bool(widgets["auto_prom"].value)
        state.baseline_on = bool(widgets["baseline_toggle"].value)
        state.baseline_degree = int(widgets["degree_input"].value or 1)
        if state.primary is not None:
            try:
                _recompute_peaks(state)
                state.error = ""
                state.status = (
                    f"{state.primary.title}: peaks={len(state.peaks)}, "
                    f"baseline={'on' if state.baseline_on else 'off'}"
                )
            except Exception as exc:  # noqa: BLE001
                state.error = f"Peak/baseline error: {exc}"
        refresh_ui()

    def on_load_overlay() -> None:
        raw = str(widgets["overlay_path_input"].value or "").strip()
        if not raw:
            state.overlay_spec = None
            state.overlay_path = ""
            state.status = "Overlay cleared"
            state.error = ""
            refresh_ui()
            return
        _load_from_path(state, raw, as_overlay=True)
        refresh_ui()

    def on_overlay_fixture(key: str) -> None:
        _load_fixture(state, key, as_overlay=True)
        refresh_ui()

    def on_clear_overlay() -> None:
        state.overlay_spec = None
        state.overlay_path = ""
        widgets["overlay_path_input"].value = ""
        state.status = "Overlay cleared"
        state.error = ""
        refresh_ui()

    async def on_upload(e) -> None:  # noqa: ANN001 — NiceGUI UploadEventArguments
        name = e.file.name
        suffix = Path(name).suffix or ".csv"
        tmp = (
            Path(tempfile.gettempdir())
            / f"chemspec_upload_{Path(name).stem}{suffix}"
        )
        await e.file.save(tmp)
        widgets["path_input"].value = str(tmp)
        on_sniff()
        on_load_path()

    with ui.row().classes("w-full q-px-md q-gutter-md items-start no-wrap"):
        with ui.card().classes("col-12 col-md-5"):
            ui.label("1 · Load spectrum").classes("text-subtitle1")
            ui.label(
                "CSV-first. Synthetic fixtures are labeled — no compound ID."
            ).classes("text-caption text-grey-7")

            widgets["path_input"] = (
                ui.input(
                    label="CSV path",
                    placeholder=str(FIXTURE_PRESETS["uvvis"]["path"]),
                    value=str(FIXTURE_PRESETS["uvvis"]["path"]),
                )
                .classes("w-full")
            )

            with ui.row().classes("q-gutter-sm"):
                ui.button("Sniff columns", on_click=on_sniff).props("outline")
                ui.button("Load path", on_click=on_load_path).props("color=primary")

            ui.upload(
                label="Or pick a CSV file",
                on_upload=on_upload,
                auto_upload=True,
            ).props('accept=".csv,text/csv"').classes("w-full")

            with ui.row().classes("q-gutter-sm q-mt-sm"):
                ui.button(
                    "Load UV-Vis fixture",
                    on_click=lambda: on_fixture("uvvis"),
                ).props("unelevated color=secondary")
                ui.button(
                    "Load IR fixture",
                    on_click=lambda: on_fixture("ir"),
                ).props("unelevated color=secondary")

            ui.separator()
            ui.label("Column mapping").classes("text-subtitle2")
            with ui.row().classes("w-full q-gutter-sm"):
                widgets["x_col_input"] = ui.input(
                    label="X column (name or index)", value="wavelength_nm"
                ).classes("col")
                widgets["y_col_input"] = ui.input(
                    label="Y column (name or index)", value="absorbance"
                ).classes("col")
            with ui.row().classes("w-full q-gutter-sm"):
                widgets["x_unit_select"] = ui.select(
                    ["nm", "cm-1"], label="X unit", value="nm"
                ).classes("col")
                widgets["y_unit_select"] = ui.select(
                    ["A", "percent_T", "intensity"],
                    label="Y unit",
                    value="A",
                ).classes("col")

            ui.separator()
            ui.label("2 · Peaks & baseline").classes("text-subtitle1")
            ui.label("Prominence").classes("text-caption")
            widgets["prom_slider"] = (
                ui.slider(min=0.01, max=1.0, step=0.01, value=0.15)
                .props("label-always")
                .classes("w-full")
            )
            widgets["auto_prom"] = ui.checkbox(
                "Auto prominence (10% y-range)", value=False
            )
            widgets["baseline_toggle"] = ui.checkbox(
                "Baseline correction (polynomial)", value=False
            )
            widgets["degree_input"] = ui.number(
                label="Baseline degree",
                value=1,
                min=0,
                max=5,
                step=1,
                format="%.0f",
            ).classes("w-40")
            ui.button("Apply", on_click=on_params_change).props("color=primary")

            ui.separator()
            ui.label("3 · Overlay second spectrum").classes("text-subtitle1")
            widgets["overlay_path_input"] = ui.input(
                label="Overlay CSV path (optional)",
                placeholder="Second spectrum path…",
            ).classes("w-full")
            with ui.row().classes("q-gutter-sm"):
                ui.button("Load overlay", on_click=on_load_overlay).props("outline")
                ui.button("Clear", on_click=on_clear_overlay).props("flat")
            with ui.row().classes("q-gutter-sm"):
                ui.button(
                    "Overlay UV-Vis fixture",
                    on_click=lambda: on_overlay_fixture("uvvis"),
                ).props("dense outline")
                ui.button(
                    "Overlay IR fixture",
                    on_click=lambda: on_overlay_fixture("ir"),
                ).props("dense outline")

        with ui.card().classes("col-12 col-md-7"):
            ui.label(
                "Interactive plot (Plotly zoom / pan / box zoom)"
            ).classes("text-subtitle1")
            widgets["plot"] = (
                ui.plotly(_build_figure(state))
                .classes("w-full")
                .style("min-height: 500px")
            )
            ui.label("Peak table").classes("text-subtitle1 q-mt-md")
            widgets["peak_table"] = ui.table(
                columns=[
                    {
                        "name": "index",
                        "label": "idx",
                        "field": "index",
                        "sortable": True,
                    },
                    {"name": "x", "label": "x", "field": "x", "sortable": True},
                    {"name": "y", "label": "y", "field": "y", "sortable": True},
                    {
                        "name": "prominence",
                        "label": "prominence",
                        "field": "prominence",
                        "sortable": True,
                    },
                ],
                rows=_peak_rows(state),
                row_key="index",
                pagination=10,
            ).classes("w-full")

    # Friendly first paint: UV-Vis synthetic fixture
    _load_fixture(state, "uvvis")
    refresh_ui()
    return state


def main() -> None:
    create_app()
    ui.run(
        title="ChemSpec Workbench",
        reload=False,
        show=False,
        port=8080,
    )


if __name__ in {"__main__", "__mp_main__"}:
    # NiceGUI may re-import as __mp_main__ when reload is enabled.
    if __name__ == "__main__":
        main()
    else:
        create_app()
