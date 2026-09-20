"""ChemSpec Workbench — interactive MVP UI (NiceGUI + Plotly).

Requires optional deps: ``pip install -e ".[ui]"`` (add ``,baselines`` for pybaselines methods)

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
    available_baseline_methods,
    baseline_correct,
    can_convert_y,
    convert_spectrum_y,
    find_peaks,
    folder_waterfall,
    has_pybaselines,
    ingest_csv,
    ingest_folder,
    ingest_jcamp,
    is_jcamp_path,
    overlay,
    peaks_to_csv,
)

from chemspec.ui_helpers import (
    FIXTURE_PRESETS,
    WATERFALL_FIXTURE_DIR,
    axis_label,
    guess_column_mapping,
    peak_export_filename,
    provenance_from_state,
    sniff_csv_header,
)

def _package_version() -> str:
    try:
        from spectrum_core import __version__ as _v

        return str(_v)
    except Exception:  # noqa: BLE001
        return ""


try:
    import plotly.graph_objects as go
    from nicegui import ui
except ImportError as exc:  # pragma: no cover - exercised only without [ui]
    raise SystemExit(
        'NiceGUI/Plotly not installed. Run: pip install -e ".[ui]"\n'
        f"Original error: {exc}"
    ) from exc


_PLOTLY_COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
]


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
        self.y_unit: str = "A"  # UV-Vis default; IR fixtures override to intensity
        self.prominence: float = 0.15
        self.use_auto_prominence: bool = False
        self.baseline_on: bool = False
        self.baseline_method: str = "polynomial"
        self.baseline_degree: int = 1
        self.flip_y_unit: bool = False  # A ↔ %T display conversion when allowed
        self.peaks: list[Peak] = []
        self.waterfall: list[Spectrum] = []
        self.waterfall_folder: str = ""
        self.waterfall_mode: bool = False
        self.status: str = "Load a CSV / JCAMP (.jdx/.dx) or pick a synthetic / public fixture to begin."
        self.error: str = ""


def _apply_y_flip(state: WorkbenchState, spec: Spectrum) -> Spectrum:
    if not state.flip_y_unit:
        return spec
    if not can_convert_y(spec.y_unit):
        return spec
    target = "percent_T" if spec.y_unit == "A" else "A"
    return convert_spectrum_y(spec, target)


def _working_spectrum(state: WorkbenchState, spec: Spectrum | None) -> Spectrum | None:
    if spec is None:
        return None
    work = spec
    if state.baseline_on:
        work = baseline_correct(
            work,
            method=state.baseline_method,
            degree=state.baseline_degree,
        )
    return _apply_y_flip(state, work)


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
    force_jcamp: bool = False,
) -> None:
    path = Path(path)
    state.error = ""
    if not path.is_file():
        state.error = f"File not found: {path}"
        return

    use_jcamp = force_jcamp or is_jcamp_path(path)

    if use_jcamp:
        try:
            spec = ingest_jcamp(path, title=title)
        except Exception as exc:  # noqa: BLE001 — surface to UI
            state.error = f"JCAMP parse failed: {exc}"
            return
        if not as_overlay:
            state.headers = []
            state.x_col = 0
            state.y_col = 1
            state.x_unit = spec.x_unit
            state.y_unit = spec.y_unit
    else:
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
        state.waterfall = []
        state.waterfall_mode = False
        state.waterfall_folder = ""
        state.flip_y_unit = False
        _recompute_peaks(state)
        state.status = (
            f"Loaded {path.name} — {len(spec)} pts, "
            f"x={spec.x_unit}, y={spec.y_unit}, peaks={len(state.peaks)}"
        )


def _load_fixture(
    state: WorkbenchState, key: str, *, as_overlay: bool = False
) -> None:
    cfg = FIXTURE_PRESETS[key]
    jcamp = cfg.get("format") == "jcamp" or is_jcamp_path(cfg["path"])
    kwargs: dict = {
        "as_overlay": as_overlay,
        "title": cfg["path"].stem,
        "force_jcamp": jcamp,
    }
    if not jcamp:
        kwargs.update(
            x_col=cfg["x_col"],
            y_col=cfg["y_col"],
            x_unit=cfg["x_unit"],
            y_unit=cfg["y_unit"],
        )
    _load_from_path(state, cfg["path"], **kwargs)
    if not as_overlay and not state.error:
        state.prominence = float(cfg["prominence"])
        state.baseline_degree = int(cfg["baseline_degree"])
        _recompute_peaks(state)
        state.status += f" (fixture: {cfg['label']})"


def _load_waterfall_folder(state: WorkbenchState, folder: Path | str) -> None:
    folder = Path(folder)
    state.error = ""
    if not folder.is_dir():
        state.error = f"Not a folder: {folder}"
        return
    try:
        raw = ingest_folder(
            folder,
            x_col=state.x_col,
            y_col=state.y_col,
            x_unit=state.x_unit,  # type: ignore[arg-type]
            y_unit=state.y_unit,  # type: ignore[arg-type]
        )
        stacked = folder_waterfall(
            folder,
            x_col=state.x_col,
            y_col=state.y_col,
            x_unit=state.x_unit,  # type: ignore[arg-type]
            y_unit=state.y_unit,  # type: ignore[arg-type]
        )
    except Exception as exc:  # noqa: BLE001
        state.error = f"Folder waterfall failed: {exc}"
        return
    if not raw:
        state.error = f"No CSV/JCAMP spectra found in {folder}"
        return
    state.waterfall = stacked
    state.waterfall_folder = str(folder)
    state.waterfall_mode = True
    state.overlay_spec = None
    state.overlay_path = ""
    state.primary = raw[0]
    state.primary_path = str(raw[0].meta.get("source", folder))
    state.x_unit = raw[0].x_unit
    state.y_unit = raw[0].y_unit
    state.flip_y_unit = False
    _recompute_peaks(state)
    state.status = (
        f"Waterfall: {len(stacked)} spectra from {folder.name} "
        f"(stacked offsets; peaks from first: {raw[0].title})"
    )


def _build_figure(state: WorkbenchState) -> go.Figure:
    fig = go.Figure()

    if state.waterfall_mode and state.waterfall:
        first = state.waterfall[0]
        xlabel, ylabel = axis_label(first.x_unit, first.y_unit)
        for i, tr in enumerate(state.waterfall):
            color = _PLOTLY_COLORS[i % len(_PLOTLY_COLORS)]
            fig.add_trace(
                go.Scatter(
                    x=tr.x.tolist(),
                    y=tr.y.tolist(),
                    mode="lines",
                    name=tr.title or f"trace_{i}",
                    line=dict(width=1.4, color=color),
                )
            )
        fig.update_layout(
            title=f"ChemSpec — waterfall ({len(state.waterfall)} stacked)",
            xaxis_title=xlabel,
            yaxis_title=f"{ylabel} (+ stack offset)",
            template="plotly_white",
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            margin=dict(l=60, r=20, t=60, b=60),
            dragmode="zoom",
        )
        if first.x_unit == "cm-1":
            fig.update_xaxes(autorange="reversed")
        fig.add_annotation(
            text="Fixtures are labeled synthetic or public — ChemSpec makes no compound-ID claims. "
            "Stack offsets are for display only.",
            xref="paper",
            yref="paper",
            x=0,
            y=-0.16,
            showarrow=False,
            font=dict(size=11, color="#666"),
            xanchor="left",
        )
        return fig

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
        label += f" (baseline {state.baseline_method})"
    if state.flip_y_unit and can_convert_y(
        state.primary.y_unit if state.primary else work.y_unit
    ):
        label += f" (as {work.y_unit})"
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
            ov_work = _working_spectrum(state, state.overlay_spec)
            assert ov_work is not None
            # overlay validates x_unit against primary working x
            pair = overlay([work, ov_work])
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
        text="Fixtures are labeled synthetic or public — ChemSpec makes no compound-ID claims.",
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
    def _round_or_none(v: float, nd: int) -> float | None:
        if v != v:  # NaN
            return None
        return round(v, nd)

    return [
        {
            "index": p.index,
            "x": round(p.x, 4),
            "y": round(p.y, 6),
            "prominence": round(p.prominence, 6),
            "fwhm": _round_or_none(p.fwhm, 6),
            "area": _round_or_none(p.area, 6),
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
        ui.label("MVP · spectrum_core · synthetic + public fixtures").classes("text-caption")

    status_label = ui.label(state.status).classes("text-body2 q-px-md q-pt-sm")
    provenance_label = ui.label("").classes(
        "text-caption text-grey-8 q-px-md font-mono"
    )
    error_label = ui.label("").classes("text-negative q-px-md")

    widgets: dict[str, Any] = {}

    def _refresh_provenance() -> None:
        primary = state.primary
        provenance_label.set_text(
            provenance_from_state(
                primary_path=state.primary_path or None,
                spectrum_title=primary.title if primary else None,
                x_unit=primary.x_unit if primary else state.x_unit,
                y_unit=primary.y_unit if primary else state.y_unit,
                baseline_on=state.baseline_on and primary is not None,
                baseline_method=state.baseline_method,
                peak_count=len(state.peaks),
                package_version=_package_version() or None,
            )
        )

    def refresh_ui() -> None:
        status_label.set_text(state.status)
        error_label.set_text(state.error or "")
        _refresh_provenance()
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
        widgets["baseline_method"].value = state.baseline_method
        widgets["degree_input"].value = state.baseline_degree
        widgets["degree_input"].set_enabled(state.baseline_method == "polynomial")
        widgets["flip_y"].value = state.flip_y_unit
        convertible = bool(
            state.primary is not None and can_convert_y(state.primary.y_unit)
        )
        widgets["flip_y"].set_enabled(convertible)
        if state.overlay_path:
            widgets["overlay_path_input"].value = state.overlay_path
        if state.waterfall_folder:
            widgets["folder_input"].value = state.waterfall_folder

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
        if is_jcamp_path(p):
            state.status = (
                f"{p.name}: JCAMP-DX detected — units come from file headers "
                "(column mapping applies to CSV only)."
            )
            state.error = ""
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
        state.baseline_method = str(widgets["baseline_method"].value or "polynomial")
        state.baseline_degree = int(widgets["degree_input"].value or 1)
        state.flip_y_unit = bool(widgets["flip_y"].value)
        if state.primary is not None:
            try:
                if state.flip_y_unit and not can_convert_y(state.primary.y_unit):
                    state.flip_y_unit = False
                    widgets["flip_y"].value = False
                    state.error = (
                        "A ↔ %T only when y_unit is A or percent_T "
                        f"(got {state.primary.y_unit!r})"
                    )
                else:
                    _recompute_peaks(state)
                    state.error = ""
                    y_note = ""
                    work = _working_spectrum(state, state.primary)
                    if work is not None and state.flip_y_unit:
                        y_note = f", display y={work.y_unit}"
                    bl = (
                        f"on/{state.baseline_method}"
                        if state.baseline_on
                        else "off"
                    )
                    state.status = (
                        f"{state.primary.title}: peaks={len(state.peaks)}, "
                        f"baseline={bl}"
                        f"{y_note}"
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
        state.waterfall_mode = False
        _load_from_path(state, raw, as_overlay=True)
        refresh_ui()

    def on_overlay_fixture(key: str) -> None:
        state.waterfall_mode = False
        _load_fixture(state, key, as_overlay=True)
        refresh_ui()

    def on_clear_overlay() -> None:
        state.overlay_spec = None
        state.overlay_path = ""
        widgets["overlay_path_input"].value = ""
        state.status = "Overlay cleared"
        state.error = ""
        refresh_ui()

    def on_export_peaks() -> None:
        if not state.peaks:
            state.error = "No peaks to export — load a spectrum and adjust prominence."
            refresh_ui()
            return
        text = peaks_to_csv(state.peaks)
        name = peak_export_filename(
            state.primary.title if state.primary else "peaks"
        )
        ui.download(text.encode("utf-8"), name)
        state.status = f"Exported {len(state.peaks)} peaks → {name}"
        state.error = ""
        refresh_ui()

    def on_load_folder() -> None:
        state.x_col = _parse_col(str(widgets["x_col_input"].value or "0"))
        state.y_col = _parse_col(str(widgets["y_col_input"].value or "1"))
        state.x_unit = str(widgets["x_unit_select"].value)
        state.y_unit = str(widgets["y_unit_select"].value)
        folder = str(widgets["folder_input"].value or "").strip()
        _load_waterfall_folder(state, folder)
        refresh_ui()

    def on_waterfall_fixture() -> None:
        state.x_col = "wavelength_nm"
        state.y_col = "absorbance"
        state.x_unit = "nm"
        state.y_unit = "A"
        widgets["folder_input"].value = str(WATERFALL_FIXTURE_DIR)
        _load_waterfall_folder(state, WATERFALL_FIXTURE_DIR)
        refresh_ui()

    def on_clear_waterfall() -> None:
        state.waterfall = []
        state.waterfall_mode = False
        state.waterfall_folder = ""
        state.status = "Waterfall cleared (primary spectrum kept)"
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
        if is_jcamp_path(tmp):
            _load_from_path(state, tmp, force_jcamp=True)
            refresh_ui()
        else:
            on_sniff()
            on_load_path()

    with ui.row().classes("w-full q-px-md q-gutter-md items-start no-wrap"):
        with ui.card().classes("col-12 col-md-5"):
            ui.label("1 · Load spectrum").classes("text-subtitle1")
            ui.label(
                "CSV-first; also .jdx/.dx (JCAMP-DX via MIT jcamp). "
                "Synthetic and public NIST/PNNL fixtures are labeled — no compound ID."
            ).classes("text-caption text-grey-7")

            widgets["path_input"] = (
                ui.input(
                    label="CSV / JCAMP path",
                    placeholder=str(FIXTURE_PRESETS["uvvis"]["path"]),
                    value=str(FIXTURE_PRESETS["uvvis"]["path"]),
                )
                .classes("w-full")
            )

            with ui.row().classes("q-gutter-sm"):
                ui.button("Sniff columns", on_click=on_sniff).props("outline")
                ui.button("Load path", on_click=on_load_path).props("color=primary")

            ui.upload(
                label="Or pick a CSV / JCAMP file",
                on_upload=on_upload,
                auto_upload=True,
            ).props('accept=".csv,.jdx,.dx,text/csv,chemical/x-jcamp-dx"').classes(
                "w-full"
            )

            with ui.row().classes("q-gutter-sm q-mt-sm"):
                ui.button(
                    "Load UV-Vis fixture",
                    on_click=lambda: on_fixture("uvvis"),
                ).props("unelevated color=secondary")
                ui.button(
                    "Load IR fixture",
                    on_click=lambda: on_fixture("ir"),
                ).props("unelevated color=secondary")
            with ui.row().classes("q-gutter-sm"):
                ui.button(
                    "Load UV-Vis JCAMP",
                    on_click=lambda: on_fixture("uvvis_jcamp"),
                ).props("outline color=secondary")
                ui.button(
                    "Load IR JCAMP",
                    on_click=lambda: on_fixture("ir_jcamp"),
                ).props("outline color=secondary")

            ui.label("Public IR (NIST / PNNL · Owner: Public domain)").classes(
                "text-caption text-grey-8 q-mt-sm"
            )
            with ui.row().classes("q-gutter-sm"):
                ui.button(
                    "Load public: Ethanol IR",
                    on_click=lambda: on_fixture("public_ethanol_ir"),
                ).props("unelevated color=primary")
                ui.button(
                    "Load public: Methanol IR",
                    on_click=lambda: on_fixture("public_methanol_ir"),
                ).props("unelevated color=primary")
                ui.button(
                    "Load public: Toluene IR",
                    on_click=lambda: on_fixture("public_toluene_ir"),
                ).props("unelevated color=primary")
            ui.label(
                "Attribution: see fixtures/public/SOURCES.md — no compound-ID claims."
            ).classes("text-caption text-grey-7")

            ui.separator()
            ui.label("Column mapping (CSV only)").classes("text-subtitle2")
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
                "Baseline correction", value=False
            )
            _bl_options = available_baseline_methods()
            if not has_pybaselines():
                ui.label(
                    'Advanced methods need: pip install -e ".[baselines]" '
                    "(pybaselines, BSD-3)."
                ).classes("text-caption text-grey-7")
            widgets["baseline_method"] = ui.select(
                _bl_options,
                label="Baseline method",
                value="polynomial",
            ).classes("w-full")
            widgets["degree_input"] = ui.number(
                label="Polynomial degree",
                value=1,
                min=0,
                max=5,
                step=1,
                format="%.0f",
            ).classes("w-40")
            ui.label(
                "Polynomial is the default/fallback. asls / mpls use optional "
                "pybaselines (BSD-3) — correction only; no compound ID."
            ).classes("text-caption text-grey-7")
            widgets["flip_y"] = ui.checkbox(
                "A ↔ %T display (when y is A or percent_T)",
                value=False,
            )
            ui.label(
                "Limits: intensity cannot convert; %T ≤ 0 or non-finite A → NaN."
            ).classes("text-caption text-grey-7")
            with ui.row().classes("q-gutter-sm"):
                ui.button("Apply", on_click=on_params_change).props("color=primary")
                ui.button("Export peaks CSV", on_click=on_export_peaks).props(
                    "outline color=primary"
                )

            ui.separator()
            ui.label("3 · Overlay second spectrum").classes("text-subtitle1")
            widgets["overlay_path_input"] = ui.input(
                label="Overlay CSV / JCAMP path (optional)",
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

            ui.separator()
            ui.label("4 · Folder waterfall").classes("text-subtitle1")
            ui.label(
                "Load a folder of CSV/JCAMP into a stacked waterfall "
                "(uses spectrum_core.stack)."
            ).classes("text-caption text-grey-7")
            widgets["folder_input"] = ui.input(
                label="Folder path",
                value=str(WATERFALL_FIXTURE_DIR),
                placeholder=str(WATERFALL_FIXTURE_DIR),
            ).classes("w-full")
            with ui.row().classes("q-gutter-sm"):
                ui.button("Load folder", on_click=on_load_folder).props(
                    "color=primary"
                )
                ui.button(
                    "Demo waterfall fixture", on_click=on_waterfall_fixture
                ).props("unelevated color=secondary")
                ui.button("Clear waterfall", on_click=on_clear_waterfall).props(
                    "flat"
                )

        with ui.card().classes("col-12 col-md-7"):
            ui.label(
                "Interactive plot (Plotly zoom / pan / box zoom)"
            ).classes("text-subtitle1")
            widgets["plot"] = (
                ui.plotly(_build_figure(state))
                .classes("w-full")
                .style("min-height: 500px")
            )
            with ui.row().classes("items-center justify-between w-full q-mt-md"):
                ui.label("Peak table").classes("text-subtitle1")
                ui.button(
                    "Download peaks CSV", on_click=on_export_peaks
                ).props("dense outline")
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
                    {
                        "name": "fwhm",
                        "label": "FWHM",
                        "field": "fwhm",
                        "sortable": True,
                    },
                    {
                        "name": "area",
                        "label": "area",
                        "field": "area",
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
