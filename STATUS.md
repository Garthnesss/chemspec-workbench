# Status — ChemSpec Workbench

**As of:** UV-Vis absorbance mapping fix + NiceGUI provenance strip

## Implemented

- `spectrum_core.Spectrum` with `x` / `y`, `x_unit` (`nm` \| `cm-1`), `y_unit` (`A` \| `percent_T` \| `intensity`), title/meta
- `ingest_csv(path, x_col, y_col, ...)` — header names or indices; `#` comments
- `ingest_jcamp(path)` — JCAMP-DX via MIT `jcamp.readfile`; maps x/y + units from headers
- `ingest(path)` — dispatches `.jdx`/`.dx` → JCAMP, else CSV
- `find_peaks` via `scipy.signal.find_peaks` (prominence configurable; default ~10% y-range)
- `baseline_polynomial` — poly fit / subtract; baseline stored in `meta`
- **`baseline_correct(spectrum, method=...)`** — polynomial always; optional **pybaselines** (BSD-3) methods `asls` / `mpls` via `[baselines]` extra; clear ImportError if missing
- `available_baseline_methods()` / `has_pybaselines()` helpers
- `overlay` / `stack` helpers for lists of spectra
- **`peaks_to_csv`** — pure peak-table CSV helper (+ UI download)
- **A ↔ %T** — `absorbance_to_percent_t` / `percent_t_to_absorbance` / `convert_spectrum_y`
  (intensity blocked; non-finite A and `%T ≤ 0` → NaN; `%T > 100` allowed with note)
- **UV-Vis fixture / guess mapping** — synthetic UV-Vis CSV meta + `guess_column_mapping`
  tag absorbance columns (`absorbance` / `A` / `AU` / `Abs` / `OD`) as `y_unit=A` so A↔%T works;
  IR `intensity` stays intensity unless header is clearly %T/A
- **Provenance strip (NiceGUI)** — `format_provenance` / `provenance_from_state` helper + UI line
  (source name, x/y units, active baseline or none, peak count, package version)
- **Folder waterfall** — `list_spectrum_files` / `ingest_folder` / `folder_waterfall` (uses `stack`)
- Synthetic fixtures: CSV + JCAMP (`uvvis_synthetic.jdx`, `ir_synthetic.dx`) + `fixtures/waterfall/`
- pytest: CSV + JCAMP ingest; peaks; baseline; units; export; folder; UI helper sniff/guess/provenance
- CLI demo: `python -m chemspec.demo`
- Matplotlib demo: `chemspec/plot_demo.py`
- **Interactive MVP UI (NiceGUI + Plotly)** — `python -m chemspec.ui_app` / `chemspec-ui`
  - CSV / JCAMP (`.jdx`/`.dx`) path + file picker; one-click UV-Vis / IR / JCAMP fixtures
  - Header sniff + simple column / unit mapping
  - Zoomable / pannable Plotly plot
  - Prominence control + peak table + **Export peaks CSV**
  - Baseline on/off + **method dropdown** (polynomial / asls / mpls) via `baseline_correct`
  - **A ↔ %T display toggle** (when units allow)
  - Overlay second spectrum (path or fixture; matching `x_unit` required)
  - **Folder waterfall** (path or demo `fixtures/waterfall/`)
- Optional extras: `pip install -e ".[ui]"` (`nicegui`, `plotly`); `pip install -e ".[baselines]"` (`pybaselines`, BSD-3); recommended UI try: `pip install -e ".[ui,baselines]"`
- Docs: README, PROJECT_TRUTH, SPEC, ROADMAP, STATUS, AGENTS
- JCAMP-DX **basic** ingest Implemented (MIT `jcamp`); clear UI error on parse failure

## Planned (not Implemented)

- Multi-user / persisted sessions (UI is local single-session MVP)
- Advanced JCAMP (multi-block LINK, complex DIFDUP edge cases, vendor quirks, certification)
- Reference peak libraries / similarity scores (Phase 1+ product; never oversell as ID)
- Hardware / TeachSpec drivers
- NMR/FID and RTL-SDR adapters (beyond stubs)
- Vendor-format certification
- Chemistry sign-off on real (non-synthetic) example files
- Time-axis metadata from filenames beyond sort-by-name / mtime (waterfall is stack offsets only)

## Blocked / human gates

- Chemistry: confirm priority lab formats + 2–3 public real example files
- Product: release claims / tags — JARTH
