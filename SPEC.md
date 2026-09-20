# ChemSpec Workbench v1 — Spec (Phase 0)

## Core package: `spectrum_core`

| Module | Responsibility |
|--------|----------------|
| `Spectrum` | x (nm \| cm⁻¹), y (A \| %T \| intensity), title/meta |
| `errors` | `SpectrumError` / `ProcessingError` hierarchy (ValueError-compatible) |
| `ingest_csv` | CSV primary via stdlib `csv` (`,`/`;`/tab, quoted fields); column index or header name; skip non-finite by default |
| `ingest_jcamp` | JCAMP-DX basic via MIT `jcamp.readfile`; unit mapping from headers; preserves x-direction |
| `ingest` | Suffix dispatch (`.jdx`/`.dx` → JCAMP; else CSV) |
| `ensure_ascending_x` / `x_direction` / `y_unit_from_header` | Optional ascending-x normalize; header→y_unit hint (ingest does not auto-flip units) |
| `find_peaks` | `scipy.signal.find_peaks`, configurable prominence; returns `Peak` with **FWHM** + **area** plus explicit contract (`width_definition`, `half_max_level`, boundaries, `area_definition`); **prominence-relative** half-height (SciPy `peak_widths` style), not absolute half-of-peak-above-zero unless prominence=0 fallback — see `spectrum_core.peaks` docstring |
| `baseline_polynomial` | poly fit / subtract (always available) |
| `baseline_correct` | dispatch: polynomial default; optional pybaselines `asls` / `mpls` (`[baselines]`, BSD-3) |
| `overlay` / `stack` | multi-spectrum helpers |
| `units` | A ↔ %T pure conversion (`convert_spectrum_y`); intensity blocked |
| `export_peaks` | `peaks_to_csv` peak table serialization (`index,x,y,prominence,fwhm,area` + contract fields) |
| `processing` | Append-only pipeline: `ProcessingHistory` / `apply_step`; ops baseline, smooth (Savitzky–Golay), despike, normalize (max\|area); preconditions raise `ProcessingError`; raw vs working via `PipelineState` |
| `session` | Versioned JSON session save/load (`.csw.json` / `.chemspec.json`, `format_version: 2`): embedded x/y + units/title, original path, processing, optional pipeline history, peaks (FWHM/area + contract), notes, provenance; **identity**: `raw_data_hash`, optional `source_path_hash`, `analysis_fingerprint` (timestamps excluded); v1 loads via migrate |
| `folder` | `ingest_folder` / `folder_waterfall` (CSV+JCAMP → stack) |
| JCAMP advanced | Planned (multi-block / certification) |

## ChemSpec layer

- CLI demo: peak table for synthetic fixtures (`python -m chemspec.demo`)
- Matplotlib plot demo: `chemspec/plot_demo.py`
- NiceGUI + Plotly MVP: optional `[ui]` extra (`python -m chemspec.ui_app`); core demos run without it
  - Peak table + CSV download (incl. FWHM/area), A↔%T display toggle, folder waterfall
  - Baseline method picker (polynomial + optional AsLS/MPLS)
  - Analysis session save/load (download / path / upload; reproducible snapshot, not compound ID)
  - Processing pipeline UI: history list, smooth + normalize + baseline steps, reset to raw

## Primary format

CSV with column mapping (primary; stdlib `csv`). JCAMP-DX basic (`.jdx`/`.dx`) via MIT `jcamp`.
Native x-order preserved (descending IR common); use `ensure_ascending_x` if needed.
Non-finite y/x rows skipped by default (`skip_nonfinite=True`); duplicate x / uneven spacing retained.
Fixtures: synthetic UV-Vis + IR (CSV and JCAMP) + `fixtures/waterfall/` + `fixtures/ingest_edge/`.


## Session file format (`.csw.json` / `.chemspec.json`)

Versioned JSON (`format_version: 2`; v1 migrates on load) for reproducible analysis sessions:

| Field | Contents |
|-------|----------|
| `format_version` | Schema version (currently `2`; supports load of `1` via migrate) |
| `software_version` | `spectrum_core` / package version string |
| `spectrum` | Embedded `x` / `y` arrays + `x_unit` / `y_unit` / `title` / `source_path` / JSON-safe `meta` |
| `processing` | `baseline_on`, `baseline_method`, `baseline_degree`, `flip_y_unit` (A↔%T display), `prominence`, `use_auto_prominence` |
| `history` | Optional append-only list of `{name,params,timestamp,software_note}` pipeline steps (replay onto raw → working). Timestamps are provenance only |
| `peaks` | List of `{index,x,y,prominence,fwhm,area,width_definition,half_max_level,left_boundary_x,right_boundary_x,area_definition,baseline_reference_note}` (non-finite → JSON `null`) |
| `notes` | Optional free-text string |
| `provenance` | Snapshot (`source`, units, baseline, peak_count, `summary` line) |
| `raw_data_hash` | SHA-256 of canonical **arrays-only** x‖y encoding (units **not** included; see `analysis_fingerprint`) |
| `source_path_hash` | Optional SHA-256 of UTF-8 `source_path` |
| `analysis_fingerprint` | SHA-256 over identity fields (raw hash, **x_unit/y_unit**, processing, history name/params, peaks). **Excludes** history timestamps / notes wall-clock. Prefer this over `raw_data_hash` alone when units matter. |

Prefer embedded arrays so reload works if the original path moves; `source_path` is retained for provenance. `spectrum` is the **raw** copy; replay `history` for the working spectrum. **Not** compound ID.

## Non-goals

Hardware, compound libraries, NMR/FID, RTL-SDR, clinical claims, SaaS.
Baseline tools correct continuum only — **no compound-ID claims**.

## LabRF Monitor (sibling, Phase 1 mock)

- Package `labrf/`: mock IQ → FFT power spectrum → `spectrum_core.Spectrum` (`Hz`/`MHz`, `dB`)
- Waterfall buffer; educational presets JSON (not regulatory advice)
- Optional pyrtlsdr behind protocol (`[labrf]` / `[rtlsdr]`); CI uses mock only
- UI: `python -m labrf.ui_app` (NiceGUI `[ui]` extra)
- Non-goals: demodulation, TX, compliance claims, chemical ID

