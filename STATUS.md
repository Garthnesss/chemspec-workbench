# Status — ChemSpec Workbench

**As of:** 2026-09-19 (PT) — Peak FWHM + area characterization + CI clean-install + public IR fixtures + LabRF polish + ChemSpec MVP

## Implemented

- `spectrum_core.Spectrum` with `x` / `y`, `x_unit` (`nm` \| `cm-1` \| `Hz` \| `MHz`), `y_unit` (`A` \| `percent_T` \| `intensity` \| `dB`), title/meta
- `ingest_csv(path, x_col, y_col, ...)` — header names or indices; `#` comments
- `ingest_jcamp(path)` — JCAMP-DX via MIT `jcamp.readfile`; maps x/y + units from headers
- `ingest(path)` — dispatches `.jdx`/`.dx` → JCAMP, else CSV
- `find_peaks` via `scipy.signal.find_peaks` (prominence configurable; default ~10% y-range)
  - Each `Peak` includes **FWHM** (`abs` half-max width; ascending/descending `x`) and **area**
    (trapezoidal integral between the same half-max bounds; see `spectrum_core.peaks` docstring)
  - NaN-safe: missing crossings / edge peaks → `fwhm`/`area` = NaN
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
- **Public IR fixtures** (`fixtures/public/`): PNNL/IARPA JCAMP ethanol / methanol / toluene
  labeled **Owner: Public domain** on NIST WebBook; `SOURCES.md` with URLs, attribution,
  NIST disclaimer; Coblentz **not** bundled; ChemSpec still makes no compound-ID claims
- pytest: CSV + JCAMP ingest; **public fixture load + ≥1 peak**; peaks (**Gaussian FWHM/area tolerances**); baseline; units; export (`fwhm`,`area` columns); folder; UI helper sniff/guess/provenance
- CLI demo: `python -m chemspec.demo`
- Matplotlib demo: `chemspec/plot_demo.py`
- **Interactive MVP UI (NiceGUI + Plotly)** — `python -m chemspec.ui_app` / `chemspec-ui`
  - CSV / JCAMP (`.jdx`/`.dx`) path + file picker; one-click UV-Vis / IR / JCAMP synthetic
    fixtures + **Load public: Ethanol/Methanol/Toluene IR**
  - Header sniff + simple column / unit mapping
  - Zoomable / pannable Plotly plot
  - Prominence control + peak table (x/y/prominence/**FWHM**/**area**) + **Export peaks CSV**
  - Baseline on/off + **method dropdown** (polynomial / asls / mpls) via `baseline_correct`
  - **A ↔ %T display toggle** (when units allow)
  - Overlay second spectrum (path or fixture; matching `x_unit` required)
  - **Folder waterfall** (path or demo `fixtures/waterfall/`)
- Optional extras: `pip install -e ".[ui]"` (`nicegui`, `plotly`); `pip install -e ".[baselines]"` (`pybaselines`, BSD-3); recommended UI try: `pip install -e ".[ui,baselines]"`
- Docs: README, PROJECT_TRUTH, SPEC, ROADMAP, STATUS, AGENTS
- **CI / clean-install** — GitHub Actions `.github/workflows/ci.yml` on push/PR to `main`:
  Python 3.11 + 3.13, `pip install -e ".[dev,ui,baselines]"`, `pytest -q`;
  `jcamp` in main deps; `make test` / `scripts/ci-test.sh` mirror CI locally
- JCAMP-DX **basic** ingest Implemented (MIT `jcamp`); clear UI error on parse failure

## LabRF Monitor (sibling app)

- Package `labrf/` — mock IQ → FFT power spectrum → `Spectrum`; waterfall buffer; educational presets JSON
- NiceGUI UI: `python -m labrf.ui_app` (port 8081); **no dongle required**
  - **Streaming mock waterfall** (Start/Stop) with successive synthetic IQ frames
  - **Threshold event log** (dB threshold → timestamped freq/level; clear; CSV export)
  - Quick preset jump buttons, Load mock fixture, provenance strip, clearer disclaimer banner
- Optional `[labrf]` / `[rtlsdr]` → pyrtlsdr adapter with clear ImportError if missing
- pytest: mock FFT, presets, waterfall, **stream generator**, **threshold logic**, RTL missing-extra guard
- Docs: `docs/family/labrf-monitor/status.md`; AGENTS receive-only / no chem-ID / educational-presets rules
- **Not** Implemented: live hardware-verified RTL captures, demodulation, TX, compliance claims

## Planned (not Implemented)

- Multi-user / persisted sessions (UI is local single-session MVP)
- Advanced JCAMP (multi-block LINK, complex DIFDUP edge cases, vendor quirks, certification)
- Reference peak libraries / similarity scores (Phase 1+ product; never oversell as ID)
- Hardware / TeachSpec drivers
- NMR/FID adapters; LabRF **live** RTL-SDR hardware-verified path (mock path Implemented)
- Vendor-format certification
- Broader chemistry sign-off / more public real examples (UV-Vis)
- Time-axis metadata from filenames beyond sort-by-name / mtime (waterfall is stack offsets only)

## Blocked / human gates

- Chemistry: confirm priority lab formats + additional public real examples (UV-Vis if openly available)
- Product: release claims / tags — JARTH
