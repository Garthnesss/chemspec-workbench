"""ChemSpec Workbench — interactive MVP UI (NiceGUI + Plotly).

Requires optional deps: ``pip install -e ".[ui]"`` (add ``,baselines`` for pybaselines methods)

Launch:
    python -m chemspec.ui_app
    # or: chemspec-ui
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from spectrum_core import (
    Peak,
    ProcessingHistory,
    SessionError,
    Spectrum,
    apply_step,
    available_baseline_methods,
    baseline_correct,
    can_convert_y,
    convert_spectrum_y,
    diagnose_measurement,
    find_peaks,
    folder_waterfall,
    has_pybaselines,
    ingest_csv,
    ingest_folder,
    ingest_jcamp,
    is_jcamp_path,
    load_session,
    overlay,
    peaks_to_csv,
    export_spectrum_png,
    export_waterfall_png,
    replay_history,
    save_session,
    session_to_dict,
)
from spectrum_core.session import session_download_filename

from chemspec.ui_helpers import (
    FIXTURE_PRESETS,
    WATERFALL_FIXTURE_DIR,
    axis_label,
    display_y_caption,
    flip_y_blocked_reason,
    format_diagnostics_strip,
    guess_column_mapping,
    is_log_epsilon_meta,
    peak_export_filename,
    png_export_filename,
    provenance_from_state,
    sniff_csv_header,
)

from chemspec.plot3d import build_surface_figure

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
        # Processing pipeline: primary = raw; working = processed copy; history append-only
        self.working: Spectrum | None = None
        self.history: ProcessingHistory = ProcessingHistory()
        self.smooth_window: int = 11
        self.smooth_polyorder: int = 3
        self.normalize_mode: str = "max"
        self.peaks: list[Peak] = []
        self.notes: str = ""
        self.waterfall: list[Spectrum] = []
        self.waterfall_folder: str = ""
        self.waterfall_mode: bool = False
        self.view_3d: bool = False  # optional Plotly surface (series index ≠ time)
        self.status: str = "Load a CSV / JCAMP (.jdx/.dx) or pick a synthetic / public fixture to begin."
        self.error: str = ""
        self.diagnostics_text: str = ""


def _apply_y_flip(state: WorkbenchState, spec: Spectrum) -> Spectrum:
    if not state.flip_y_unit:
        return spec
    if not can_convert_y(spec.y_unit):
        return spec
    target = "percent_T" if spec.y_unit == "A" else "A"
    return convert_spectrum_y(spec, target)


def _reset_pipeline(state: WorkbenchState) -> None:
    """Set working = copy of raw primary; clear history."""
    if state.primary is None:
        state.working = None
        state.history = ProcessingHistory()
        return
    state.working = state.primary.copy()
    state.history = ProcessingHistory()


def _working_spectrum(state: WorkbenchState, spec: Spectrum | None) -> Spectrum | None:
    """Return display/analysis spectrum without mutating raw ``primary``.

    For the primary trace, prefer ``state.working`` (pipeline result). When
    history is empty, the legacy baseline toggle still applies on the fly.
    Overlay uses the live baseline toggle only (no shared history).
    """
    if spec is None:
        return None
    if spec is state.primary:
        work = state.working if state.working is not None else spec
        # Guard: if working was left over from a previous primary, discard it.
        if (
            work is not state.primary
            and (
                len(work) != len(state.primary)
                or work.x_unit != state.primary.x_unit
            )
        ):
            work = state.primary
            state.working = state.primary.copy()
            state.history = ProcessingHistory()
        if len(state.history) == 0 and state.baseline_on:
            work = baseline_correct(
                state.primary,
                method=state.baseline_method,
                degree=state.baseline_degree,
            )
    else:
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
        state.diagnostics_text = ""
        return
    state.peaks = find_peaks(work, prominence=_prominence_arg(state))
    baseline_applied = bool(state.baseline_on) or (
        "baseline_method" in (work.meta or {})
    ) or any(s.name == "baseline" for s in state.history.steps)
    diag = diagnose_measurement(
        work,
        state.peaks,
        baseline_applied=baseline_applied,
    )
    state.diagnostics_text = format_diagnostics_strip(diag)


def _processing_from_state(state: WorkbenchState) -> dict[str, Any]:
    return {
        "baseline_on": bool(state.baseline_on),
        "baseline_method": str(state.baseline_method or "polynomial"),
        "baseline_degree": int(state.baseline_degree),
        "flip_y_unit": bool(state.flip_y_unit),
        "prominence": float(state.prominence),
        "use_auto_prominence": bool(state.use_auto_prominence),
    }


def _load_session_path(state: WorkbenchState, path: Path | str) -> None:
    """Load a .csw.json / .chemspec.json session into workbench state."""
    path = Path(path)
    state.error = ""
    try:
        data = load_session(path)
    except SessionError as exc:
        state.error = f"Session load failed: {exc}"
        return
    except Exception as exc:  # noqa: BLE001
        state.error = f"Session load failed: {exc}"
        return

    state.primary = data.spectrum
    state.primary_path = data.source_path or str(path)
    state.overlay_spec = None
    state.overlay_path = ""
    state.waterfall = []
    state.waterfall_mode = False
    state.waterfall_folder = ""
    state.headers = []
    state.x_col = 0
    state.y_col = 1
    state.x_unit = data.spectrum.x_unit
    state.y_unit = data.spectrum.y_unit
    proc = data.processing
    state.baseline_on = bool(proc.get("baseline_on", False))
    state.baseline_method = str(proc.get("baseline_method") or "polynomial")
    state.baseline_degree = int(proc.get("baseline_degree", 1))
    state.flip_y_unit = bool(proc.get("flip_y_unit", False))
    state.prominence = float(proc.get("prominence", 0.15))
    state.use_auto_prominence = bool(proc.get("use_auto_prominence", False))
    state.notes = data.notes or ""
    # Replay pipeline history onto working; raw primary stays as embedded spectrum
    try:
        if len(data.history) > 0:
            state.working, state.history = replay_history(data.spectrum, data.history)
            # History owns baseline; avoid double-applying live toggle
            state.baseline_on = False
        else:
            _reset_pipeline(state)
    except Exception as exc:  # noqa: BLE001
        state.error = f"Session history replay failed: {exc}"
        _reset_pipeline(state)
    # Prefer stored peaks (reproducible snapshot); fall back to recompute
    if data.peaks:
        state.peaks = list(data.peaks)
    else:
        _recompute_peaks(state)
    n_pts = len(data.spectrum)
    n_hist = len(state.history)
    if n_hist > 0:
        hist_note = (
            f"replayed {n_hist} pipeline step(s) onto working "
            "(raw spectrum preserved; live baseline toggle off)"
        )
    else:
        hist_note = "no pipeline history (working = raw copy)"
    state.status = (
        f"Session loaded: {path.name} — {n_pts} pts, "
        f"peaks={len(state.peaks)}, {hist_note}"
    )


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
        # New primary must not keep a prior fixture's working buffer / history
        # (otherwise plot + peaks stay on the previous spectrum after reload).
        state.baseline_on = False
        _reset_pipeline(state)
        _recompute_peaks(state)
        state.status = (
            f"Loaded {path.name} — {len(spec)} pts, "
            f"x={spec.x_unit}, y={spec.y_unit}, peaks={len(state.peaks)}"
        )
        if is_log_epsilon_meta(spec.meta):
            state.status += (
                " · y is log₁₀(ε) stored as intensity — not absorbance; "
                "A ↔ %T disabled"
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
    _reset_pipeline(state)
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
        # Optional 3-D surface: series index ≠ time; needs ≥2 traces (docs/viz3d.md)
        if state.view_3d and len(state.waterfall) >= 2:
            return build_surface_figure(state.waterfall, xlabel, ylabel)
        warn_3d = state.view_3d and len(state.waterfall) < 2
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
        title = f"ChemSpec — waterfall ({len(state.waterfall)} stacked)"
        if warn_3d:
            title += " — 3-D needs ≥2 traces"
        fig.update_layout(
            title=title,
            xaxis_title=xlabel,
            yaxis_title=f"{ylabel} (+ stack offset)",
            template="plotly_white",
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            margin=dict(l=60, r=20, t=60, b=80 if warn_3d else 60),
            dragmode="zoom",
        )
        if first.x_unit == "cm-1":
            fig.update_xaxes(autorange="reversed")
        footer = (
            "Fixtures are labeled synthetic or public — ChemSpec makes no compound-ID claims. "
            "Stack offsets are for display only."
        )
        if warn_3d:
            footer = (
                "3-D surface needs at least two folder traces. "
                "Series index is folder order — not a time axis. "
                "ChemSpec makes no compound-ID claims."
            )
        fig.add_annotation(
            text=footer,
            xref="paper",
            yref="paper",
            x=0,
            y=-0.18 if warn_3d else -0.16,
            showarrow=False,
            font=dict(size=11, color="#888" if warn_3d else "#666"),
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

    xlabel, _ = axis_label(work.x_unit, work.y_unit)
    ylabel = display_y_caption(work.y_unit, work.meta)
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
            "half_max": _round_or_none(p.half_max_level, 6),
            "left_x": _round_or_none(p.left_boundary_x, 4),
            "right_x": _round_or_none(p.right_boundary_x, 4),
            "width_def": p.width_definition,
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
    diagnostics_label = ui.label("").classes(
        "text-caption text-amber-9 q-px-md q-pb-sm"
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
        diagnostics_label.set_text(state.diagnostics_text or "")
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
        if "y_caption" in widgets:
            if state.primary is not None:
                widgets["y_caption"].set_text(
                    "Y axis: "
                    + display_y_caption(state.primary.y_unit, state.primary.meta)
                )
            else:
                widgets["y_caption"].set_text("Y axis: (no spectrum)")
        if "flip_y_warn" in widgets:
            if state.primary is not None and not convertible:
                reason = flip_y_blocked_reason(
                    state.primary.y_unit, state.primary.meta
                )
                widgets["flip_y_warn"].set_text(reason or "")
            elif convertible:
                widgets["flip_y_warn"].set_text(
                    "Limits: %T ≤ 0 or non-finite A → NaN."
                )
            else:
                widgets["flip_y_warn"].set_text(
                    "Limits: intensity cannot convert; %T ≤ 0 or non-finite A → NaN."
                )
        if "notes_input" in widgets:
            widgets["notes_input"].value = state.notes
        if "session_path_input" in widgets and state.primary_path.endswith(
            (".csw.json", ".chemspec.json")
        ):
            widgets["session_path_input"].value = state.primary_path
        if state.overlay_path:
            widgets["overlay_path_input"].value = state.overlay_path
        if state.waterfall_folder:
            widgets["folder_input"].value = state.waterfall_folder
        if "view_3d" in widgets:
            if bool(widgets["view_3d"].value) != state.view_3d:
                widgets["view_3d"].value = state.view_3d
            n_wf = len(state.waterfall) if state.waterfall_mode else 0
            widgets["view_3d"].set_enabled(n_wf >= 2)
            if "view_3d_hint" in widgets:
                if n_wf >= 2:
                    widgets["view_3d_hint"].set_text(
                        "Series index = folder order (not time). No compound ID."
                    )
                elif state.waterfall_mode:
                    widgets["view_3d_hint"].set_text(
                        "3-D surface needs ≥2 folder traces (disabled)."
                    )
                else:
                    widgets["view_3d_hint"].set_text(
                        "Load a folder waterfall (≥2 traces) to enable 3-D surface."
                    )
        if "history_list" in widgets:
            lines = state.history.summary_lines()
            widgets["history_list"].set_text(
                "\n".join(lines) if lines else "(no pipeline steps — raw)"
            )
        if "smooth_window" in widgets:
            widgets["smooth_window"].value = state.smooth_window
            widgets["smooth_polyorder"].value = state.smooth_polyorder
            widgets["normalize_mode"].value = state.normalize_mode

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
                    state.error = flip_y_blocked_reason(
                        state.primary.y_unit, state.primary.meta
                    ) or (
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


    def on_export_plot_png() -> None:
        """Matplotlib PNG with honesty footer (parity with LabRF export)."""
        import io

        if state.waterfall_mode and state.waterfall:
            buf = io.BytesIO()
            export_waterfall_png(state.waterfall, buf)
            name = "chemspec_waterfall.png"
            ui.download(buf.getvalue(), name)
            state.status = f"Exported waterfall PNG → {name}"
            state.error = ""
            refresh_ui()
            return

        work = _working_spectrum(state, state.primary)
        if work is None:
            state.error = "No spectrum to export — load a spectrum first."
            refresh_ui()
            return
        ov = None
        if state.overlay_spec is not None:
            try:
                ov = _working_spectrum(state, state.overlay_spec)
            except Exception:  # noqa: BLE001
                ov = state.overlay_spec
        buf = io.BytesIO()
        export_spectrum_png(
            work,
            buf,
            peaks=state.peaks or None,
            overlay=ov,
            title=f"ChemSpec — {work.title}",
        )
        name = png_export_filename(work.title)
        ui.download(buf.getvalue(), name)
        state.status = f"Exported spectrum PNG → {name}"
        state.error = ""
        refresh_ui()

    def on_save_session() -> None:
        if state.primary is None:
            state.error = "No spectrum to save — load a spectrum first."
            refresh_ui()
            return
        if "notes_input" in widgets:
            state.notes = str(widgets["notes_input"].value or "")
        try:
            payload = session_to_dict(
                state.primary,
                processing=_processing_from_state(state),
                peaks=state.peaks,
                notes=state.notes,
                source_path=state.primary_path or None,
                history=state.history,
            )
        except Exception as exc:  # noqa: BLE001
            state.error = f"Session save failed: {exc}"
            refresh_ui()
            return
        name = session_download_filename(
            state.primary.title if state.primary else "session"
        )
        body = json.dumps(payload, indent=2, allow_nan=False) + "\n"
        ui.download(body.encode("utf-8"), name)
        state.status = (
            f"Saved session → {name} "
            f"(format_version={payload['format_version']}, "
            f"peaks={len(state.peaks)})"
        )
        state.error = ""
        refresh_ui()

    def on_load_session_path() -> None:
        raw = str(widgets["session_path_input"].value or "").strip()
        if not raw:
            state.error = "Enter a session path (.csw.json / .chemspec.json)."
            refresh_ui()
            return
        _load_session_path(state, raw)
        refresh_ui()

    async def on_session_upload(e) -> None:  # noqa: ANN001
        name = e.file.name
        # Allow .json / .csw.json / .chemspec.json
        tmp = (
            Path(tempfile.gettempdir())
            / f"chemspec_session_{Path(name).name}"
        )
        await e.file.save(tmp)
        widgets["session_path_input"].value = str(tmp)
        _load_session_path(state, tmp)
        refresh_ui()

    def on_save_session_to_path() -> None:
        if state.primary is None:
            state.error = "No spectrum to save — load a spectrum first."
            refresh_ui()
            return
        raw = str(widgets["session_path_input"].value or "").strip()
        if not raw:
            # default under temp
            raw = str(
                Path(tempfile.gettempdir())
                / session_download_filename(
                    state.primary.title if state.primary else "session"
                )
            )
            widgets["session_path_input"].value = raw
        if "notes_input" in widgets:
            state.notes = str(widgets["notes_input"].value or "")
        try:
            save_session(
                raw,
                state.primary,
                processing=_processing_from_state(state),
                peaks=state.peaks,
                notes=state.notes,
                source_path=state.primary_path or None,
                history=state.history,
            )
        except Exception as exc:  # noqa: BLE001
            state.error = f"Session save failed: {exc}"
            refresh_ui()
            return
        state.status = f"Wrote session file: {raw}"
        state.error = ""
        refresh_ui()

    def _sync_pipeline_widgets() -> None:
        state.baseline_method = str(widgets["baseline_method"].value or "polynomial")
        state.baseline_degree = int(widgets["degree_input"].value or 1)
        state.smooth_window = int(widgets["smooth_window"].value or 11)
        state.smooth_polyorder = int(widgets["smooth_polyorder"].value or 3)
        state.normalize_mode = str(widgets["normalize_mode"].value or "max")

    def _apply_pipeline_step(name: str, params: dict) -> None:
        if state.primary is None:
            state.error = "Load a spectrum before applying pipeline steps."
            refresh_ui()
            return
        if state.working is None:
            _reset_pipeline(state)
        try:
            state.working, state.history = apply_step(
                state.working, state.history, name, params
            )
            # Pipeline owns transforms; clear live baseline toggle to avoid double apply
            state.baseline_on = False
            widgets["baseline_toggle"].value = False
            _recompute_peaks(state)
            state.error = ""
            state.status = (
                f"Applied {name} — history={len(state.history)}, "
                f"peaks={len(state.peaks)}"
            )
        except Exception as exc:  # noqa: BLE001
            state.error = f"Pipeline {name} failed: {exc}"
        refresh_ui()

    def on_apply_baseline_step() -> None:
        _sync_pipeline_widgets()
        _apply_pipeline_step(
            "baseline",
            {
                "method": state.baseline_method,
                "degree": state.baseline_degree,
            },
        )

    def on_apply_smooth_step() -> None:
        _sync_pipeline_widgets()
        _apply_pipeline_step(
            "smooth",
            {
                "window_length": state.smooth_window,
                "polyorder": state.smooth_polyorder,
            },
        )

    def on_apply_normalize_step() -> None:
        _sync_pipeline_widgets()
        _apply_pipeline_step("normalize", {"mode": state.normalize_mode})

    def on_reset_to_raw() -> None:
        if state.primary is None:
            state.error = "Nothing to reset — load a spectrum first."
            refresh_ui()
            return
        _reset_pipeline(state)
        state.baseline_on = False
        widgets["baseline_toggle"].value = False
        _recompute_peaks(state)
        state.error = ""
        state.status = f"Reset to raw — {state.primary.title} ({len(state.primary)} pts)"
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

    def on_view_3d_change() -> None:
        new_val = bool(widgets["view_3d"].value)
        if new_val == state.view_3d:
            return  # ignore refresh_ui value sync
        state.view_3d = new_val
        n = len(state.waterfall) if state.waterfall_mode else 0
        if state.view_3d and n < 2:
            state.status = (
                "3-D surface needs ≥2 waterfall traces "
                "(series index ≠ time; no compound ID)."
            )
        elif state.view_3d and n >= 2:
            state.status = (
                f"3-D surface on — {n} traces (series index, not time; "
                "stack offsets stripped). No compound ID."
            )
        elif state.waterfall_mode:
            state.status = f"2-D waterfall ({n} stacked)"
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
                "Public UV-Vis (NIST WebBook · YUNITS=Logarithm epsilon → intensity)"
            ).classes("text-caption text-grey-8 q-mt-sm")
            with ui.row().classes("q-gutter-sm"):
                ui.button(
                    "Load public: Benzene UV-Vis",
                    on_click=lambda: on_fixture("public_benzene_uvvis"),
                ).props("unelevated color=primary")
                ui.button(
                    "Load public: Acetone UV-Vis",
                    on_click=lambda: on_fixture("public_acetone_uvvis"),
                ).props("unelevated color=primary")
                ui.button(
                    "Load public: Naphthalene UV-Vis",
                    on_click=lambda: on_fixture("public_naphthalene_uvvis"),
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

            ui.separator()
            ui.label("2a · Processing pipeline").classes("text-subtitle1")
            ui.label(
                "Append-only steps on a working copy; raw spectrum is never mutated. "
                "Ops: baseline · smooth (Savitzky–Golay) · normalize (max|area). "
                "Optional despike is available in spectrum_core. Not compound ID."
            ).classes("text-caption text-grey-7")
            with ui.row().classes("w-full q-gutter-sm"):
                widgets["smooth_window"] = ui.number(
                    label="Smooth window (odd)",
                    value=11,
                    min=3,
                    max=101,
                    step=2,
                    format="%.0f",
                ).classes("col")
                widgets["smooth_polyorder"] = ui.number(
                    label="Smooth polyorder",
                    value=3,
                    min=0,
                    max=5,
                    step=1,
                    format="%.0f",
                ).classes("col")
            widgets["normalize_mode"] = ui.select(
                ["max", "area"],
                label="Normalize mode",
                value="max",
            ).classes("w-full")
            with ui.row().classes("q-gutter-sm"):
                ui.button(
                    "Apply baseline", on_click=on_apply_baseline_step
                ).props("outline color=primary")
                ui.button(
                    "Apply smooth", on_click=on_apply_smooth_step
                ).props("outline color=primary")
                ui.button(
                    "Apply normalize", on_click=on_apply_normalize_step
                ).props("outline color=primary")
                ui.button("Reset to raw", on_click=on_reset_to_raw).props(
                    "flat color=negative"
                )
            ui.label("History").classes("text-caption")
            widgets["history_list"] = ui.label("(no pipeline steps — raw)").classes(
                "text-caption font-mono text-grey-8"
            ).style("white-space: pre-wrap")

            widgets["y_caption"] = ui.label("Y axis: (no spectrum)").classes(
                "text-caption text-grey-8 font-mono"
            )
            widgets["flip_y"] = ui.checkbox(
                "A ↔ %T display (when y is A or percent_T)",
                value=False,
            )
            widgets["flip_y_warn"] = ui.label(
                "Limits: intensity cannot convert; %T ≤ 0 or non-finite A → NaN."
            ).classes("text-caption text-grey-7")
            with ui.row().classes("q-gutter-sm"):
                ui.button("Apply", on_click=on_params_change).props("color=primary")
                ui.button("Export peaks CSV", on_click=on_export_peaks).props(
                    "outline color=primary"
                )
                ui.button("Export plot PNG", on_click=on_export_plot_png).props(
                    "outline color=primary"
                )

            ui.separator()
            ui.label("2b · Analysis session").classes("text-subtitle1")
            ui.label(
                "Save / load a versioned .csw.json (or .chemspec.json) with "
                "embedded raw spectrum, processing, pipeline history, peaks, notes, and provenance. "
                "On load, pipeline history is auto-replayed onto a working copy "
                "(raw stays unchanged; section 2a lists the steps). "
                "Reproducible analysis snapshot — not compound ID."
            ).classes("text-caption text-grey-7")
            widgets["notes_input"] = ui.textarea(
                label="Notes (optional)",
                placeholder="Lab notes for this analysis…",
                value=state.notes,
            ).classes("w-full").props("rows=2")
            widgets["session_path_input"] = ui.input(
                label="Session path (.csw.json / .chemspec.json)",
                placeholder="/path/to/analysis.csw.json",
            ).classes("w-full")
            with ui.row().classes("q-gutter-sm"):
                ui.button("Save session (download)", on_click=on_save_session).props(
                    "color=primary"
                )
                ui.button("Write session path", on_click=on_save_session_to_path).props(
                    "outline"
                )
                ui.button("Load session path", on_click=on_load_session_path).props(
                    "outline color=primary"
                )
            ui.upload(
                label="Or upload a session file",
                on_upload=on_session_upload,
                auto_upload=True,
            ).props('accept=".json,.csw.json,.chemspec.json,application/json"').classes(
                "w-full"
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
                "(uses spectrum_core.stack). Optional 3-D surface: "
                "series index ≠ time; no compound ID — see docs/viz3d.md."
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
            widgets["view_3d"] = ui.checkbox(
                "3-D surface view (series index ≠ time)",
                value=state.view_3d,
                on_change=on_view_3d_change,
            )
            widgets["view_3d"].set_enabled(False)
            widgets["view_3d_hint"] = ui.label(
                "Load a folder waterfall (≥2 traces) to enable 3-D surface."
            ).classes("text-caption text-grey-7")

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
                with ui.row().classes("q-gutter-sm"):
                    ui.button(
                        "Download peaks CSV", on_click=on_export_peaks
                    ).props("dense outline")
                    ui.button(
                        "Download plot PNG", on_click=on_export_plot_png
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
                    {
                        "name": "half_max",
                        "label": "half-max",
                        "field": "half_max",
                        "sortable": True,
                    },
                    {
                        "name": "left_x",
                        "label": "left x",
                        "field": "left_x",
                        "sortable": True,
                    },
                    {
                        "name": "right_x",
                        "label": "right x",
                        "field": "right_x",
                        "sortable": True,
                    },
                    {
                        "name": "width_def",
                        "label": "width def",
                        "field": "width_def",
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
