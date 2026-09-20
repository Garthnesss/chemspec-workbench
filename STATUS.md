# Status — ChemSpec Workbench

**As of:** 2026-09-19 (PT) — TeachSpec Phase-0 software stub + Folder-waterfall tests + README Quick demo; CI setuptools/pip-audit + NiceGUI API drift + LabRF NiceGUI 3.x + ingest hardening + Ethanol IR + LICENSE/Dependabot + Processing/Session/peaks/public IR/LabRF/MVP

## Implemented

- `spectrum_core.Spectrum` with `x` / `y`, `x_unit` (`nm` \| `cm-1` \| `Hz` \| `MHz`), `y_unit` (`A` \| `percent_T` \| `intensity` \| `dB`), title/meta
- `ingest_csv(path, x_col, y_col, ...)` — stdlib `csv` (`,`/`;`/tab, quoted fields); header names or indices; `#` comments; default skip NaN/Inf; missing cells skipped; extra cols ignored
- `ingest_jcamp(path)` — JCAMP-DX via MIT `jcamp.readfile`; maps x/y + units from headers; preserves x-direction (often descending IR)
- `ingest(path)` — dispatches `.jdx`/`.dx` → JCAMP, else CSV
- `ensure_ascending_x` / `x_direction` / `y_unit_from_header` — optional ascending-x normalize; header→`A`/`percent_T` hint (ingest does not auto-override caller units)
- **Ingest edge fixtures** (`fixtures/ingest_edge/`) — descending x, duplicates, uneven spacing, NaN/Inf, delimiters/quotes, missing/extra cols, %T vs Absorbance, empty/bad JCAMP
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
- **Analysis session save/load** — `spectrum_core.session` (`save_session` / `load_session`)
  versioned JSON (`.csw.json` / `.chemspec.json`, `format_version: 1`): embedded x/y + units/title,
  original `source_path`, processing (baseline method/params, A↔%T display, prominence),
  optional append-only pipeline `history`, peaks (incl. FWHM/area), optional notes, provenance snapshot;
  schema validation + round-trip tests; NiceGUI download / path write / path load / upload — **not** compound ID
- **Processing pipeline + history** — `spectrum_core.processing`:
  `ProcessingStep` / `ProcessingHistory` (name, params, timestamp, software_note; append-only);
  `apply_step(spectrum, history, step) → (new_spectrum, history)`; `PipelineState` keeps raw vs working;
  ops: **baseline** (reuse `baseline_correct`), **smooth** (Savitzky–Golay), **despike** (median/z-score style),
  **normalize** (max or area); session stores history; UI history list + smooth/normalize/baseline + reset to raw
- **Folder waterfall** — `list_spectrum_files` / `ingest_folder` / `folder_waterfall` (uses `stack`)
- Synthetic fixtures: CSV + JCAMP (`uvvis_synthetic.jdx`, `ir_synthetic.dx`) + `fixtures/waterfall/`
- **Public IR fixtures** (`fixtures/public/`): PNNL/IARPA JCAMP ethanol / methanol / toluene
  labeled **Owner: Public domain** on NIST WebBook; `SOURCES.md` with URLs, attribution,
  NIST disclaimer; Coblentz **not** bundled; ChemSpec still makes no compound-ID claims
- pytest: CSV + JCAMP ingest (**edge hardening**); **public fixture load + ≥1 peak**; peaks (**Gaussian FWHM/area tolerances**); baseline; units; export (`fwhm`,`area` columns); folder (**mtime/recursive/hidden skip/auto-offset**); UI helper sniff/guess/provenance; **session save/load round-trip + schema**; **processing ops + history round-trip + session integration**
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
  - **Session save/load** (download `.csw.json`, write/load path, upload; notes field; stores pipeline history)
  - **Processing pipeline** (history list; Apply baseline / smooth / normalize; Reset to raw)
- Optional extras: `pip install -e ".[ui]"` (`nicegui`, `plotly`); `pip install -e ".[baselines]"` (`pybaselines`, BSD-3); recommended UI try: `pip install -e ".[ui,baselines]"`
- **Ethanol IR tutorial** — `examples/ethanol_ir_walkthrough.ipynb` (+ `.py` twin):
  load public `ethanol_ir_pnnl.jdx`, cite `SOURCES.md`, plot (matplotlib), pipeline
  baseline+smooth, peaks with FWHM/area, optional peaks CSV / `.csw.json` session;
  clear no-compound-ID disclaimer; pytest smoke on the script (no nbconvert in CI yet)
- Docs: README (**Quick demo** + **Folder waterfall** multi-file section), PROJECT_TRUTH, SPEC, ROADMAP, STATUS, AGENTS, `examples/README.md`, `fixtures/waterfall/README.md`
- **CI / clean-install** — GitHub Actions `.github/workflows/ci.yml` on push/PR to `main`:
  Python 3.11 + 3.13, `pip install -e ".[dev,ui,baselines]"`, upgrade **`setuptools>=83`** then **`pip-audit`**
  (avoids GHA 3.11 image setuptools 79 advisory), LabRF `build_ui` smoke, `pytest -q`;
  `jcamp` in main deps; `make test` / `scripts/ci-test.sh` mirror CI locally;
  NiceGUI API-drift tests assert every `ui.*` used by LabRF/ChemSpec exists
- **License + Dependabot** — root `LICENSE` (MIT, ChemSpec Workbench contributors, 2026); `.github/dependabot.yml` weekly for pip + github-actions
- JCAMP-DX **basic** ingest Implemented (MIT `jcamp`); clear UI error on parse failure

## LabRF Monitor (sibling app)

- Package `labrf/` — mock IQ → FFT power spectrum → `Spectrum`; waterfall buffer; educational presets JSON
- NiceGUI UI: `python -m labrf.ui_app` (port 8081); **no dongle required**
  - Compatible with **NiceGUI 3.x** (disclaimer uses dismissible `ui.card`, not removed `ui.banner`); CI/API-drift guards
  - **Streaming mock waterfall** (Start/Stop) with successive synthetic IQ frames
  - **Threshold event log** (dB threshold → timestamped freq/level; clear; CSV export; maxlen-capped)
  - Waterfall auto-reset on retune; mock configure no-op when unchanged; vectorized fixture ring-read
  - Quick preset jump buttons, Load mock fixture, provenance strip, clearer dismissible disclaimer card
- Optional `[labrf]` / `[rtlsdr]` → pyrtlsdr adapter with clear ImportError if missing
- pytest: mock FFT, presets, waterfall, **stream generator**, **threshold logic**, RTL missing-extra guard
- Docs: `docs/family/labrf-monitor/status.md`; AGENTS receive-only / no chem-ID / educational-presets rules
- **Not** Implemented: live hardware-verified RTL captures, demodulation, TX, compliance claims


## TeachSpec (sibling — Phase 0 software stub)

- Package `teachspec/` — educational optical teaching spectrometer **software** path only
  - Pixel→nm linear (+ optional quadratic) calibration from ≥2 known lines; JSON save/load
  - `OpticalLiveFrame` → `spectrum_core.Spectrum` after calibration
  - Synthetic CFL-like mock frames (`mock_source`); CLI `python -m teachspec.demo` / `teachspec-demo`
  - pytest: fit correctness, bad inputs (1 point / duplicates), mock→Spectrum peaks, cal I/O
- Docs: `docs/family/teachspec/` status/roadmap updated — software stub *Implemented*
- **Not** Implemented: USB-cam vs linear CCD choice, BOM, live camera/CCD drivers, hardware-verified calibration, compound ID

## Planned (not Implemented)

- Multi-user / cloud-persisted sessions (local `.csw.json` save/load is Implemented)
- Advanced JCAMP (multi-block LINK, complex DIFDUP edge cases, vendor quirks, certification)
- Reference peak libraries / similarity scores (Phase 1+ product; never oversell as ID)
- TeachSpec live camera / CCD drivers + sensor lock + BOM (Phase-0 software stub Implemented)
- Hardware drivers beyond mock paths
- NMR/FID adapters; LabRF **live** RTL-SDR hardware-verified path (mock path Implemented)
- Vendor-format certification
- Broader chemistry sign-off / more public real examples (UV-Vis)
- Time-axis metadata from filenames beyond sort-by-name / mtime (waterfall is stack offsets only)

## Blocked / human gates

- Chemistry: confirm priority lab formats + additional public real examples (UV-Vis if openly available)
- Product: release claims / tags — JARTH
- TeachSpec: USB-cam vs linear CCD sensor choice; Chemistry classroom safety review; BOM pricing
