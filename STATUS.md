# Status — ChemSpec Workbench

**As of:** MVP interactive UI (NiceGUI) on `spectrum_core`

## Implemented

- `spectrum_core.Spectrum` with `x` / `y`, `x_unit` (`nm` \| `cm-1`), `y_unit` (`A` \| `percent_T` \| `intensity`), title/meta
- `ingest_csv(path, x_col, y_col, ...)` — header names or indices; `#` comments
- `find_peaks` via `scipy.signal.find_peaks` (prominence configurable; default ~10% y-range)
- `baseline_polynomial` — poly fit / subtract; baseline stored in `meta`
- `overlay` / `stack` helpers for lists of spectra
- Synthetic fixtures: `fixtures/uvvis_synthetic.csv`, `fixtures/ir_synthetic.csv`
- pytest: ingest loads fixtures; peaks within tolerance; baseline keeps peaks; UI helper sniff/guess
- CLI demo: `python -m chemspec.demo`
- Matplotlib demo: `chemspec/plot_demo.py`
- **Interactive MVP UI (NiceGUI + Plotly)** — `python -m chemspec.ui_app` / `chemspec-ui`
  - CSV path + file picker; one-click UV-Vis / IR fixtures
  - Header sniff + simple column / unit mapping
  - Zoomable / pannable Plotly plot
  - Prominence control + peak table
  - Baseline on/off via `baseline_polynomial`
  - Overlay second spectrum (path or fixture; matching `x_unit` required)
- Optional extra: `pip install -e ".[ui]"` (`nicegui`, `plotly`)
- Docs: README, PROJECT_TRUTH, SPEC, ROADMAP, STATUS, AGENTS
- JCAMP stub that raises `NotImplementedError` (explicit non-claim)

## Planned (not Implemented)

- Absorbance ↔ transmittance toggle helper
- Peak table export / CSV download from UI
- Folder waterfall for time-stamped spectra
- Multi-user / persisted sessions (UI is local single-session MVP)
- JCAMP-DX real parser
- Reference peak libraries / similarity scores (Phase 1+ product; never oversell as ID)
- Hardware / TeachSpec drivers
- NMR/FID and RTL-SDR adapters (beyond stubs)
- Vendor-format certification
- Chemistry sign-off on real (non-synthetic) example files

## Blocked / human gates

- Chemistry: confirm priority lab formats + 2–3 public real example files
- Product: release claims / tags — JARTH
