# ChemSpec Workbench

Software-only workbench for **UV-Vis / IR** spectra: open CSV, plot, find peaks,
correct a simple baseline, overlay/stack traces. Built on a reusable
`spectrum_core` package (Spectrum Family).

**Honesty:** Phase 0 / MVP does **not** identify compounds, drive spectrometers, or
read NMR/FID/RTL-SDR. Synthetic fixtures are labeled as synthetic.

## Install

```bash
cd chemspec-workbench
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Interactive UI (NiceGUI)

```bash
pip install -e ".[ui]"
# or with tests: pip install -e ".[dev,ui]"
python -m chemspec.ui_app
# or: chemspec-ui
```

Then open **http://localhost:8080**. The app autoloads the UV-Vis synthetic
fixture. You can:

- Load a CSV or JCAMP-DX (`.jdx` / `.dx`) by path or file picker; sniff / map CSV columns
- Zoom and pan the Plotly plot
- Tune peak prominence and view the peak table
- Toggle polynomial baseline correction
- Overlay a second spectrum (path or the other fixture; units must match)

Core demos still run **without** `[ui]`.

## Test

```bash
pytest
```

## Run demos (no UI)

Peak table (CLI):

```bash
python -m chemspec.demo
python -m chemspec.demo --fixture ir
# or: chemspec-demo --fixture uvvis
```

Matplotlib plot:

```bash
python chemspec/plot_demo.py
python chemspec/plot_demo.py --fixture ir --save ir_demo.png --no-show
```

## Layout

| Path | Role |
|------|------|
| `spectrum_core/` | Shared Spectrum model, CSV + JCAMP ingest, peaks, baseline, overlay/stack |
| `chemspec/` | Demos + NiceGUI MVP (`ui_app`, `ui_helpers`) |
| `fixtures/` | Synthetic UV-Vis + IR CSVs and JCAMP-DX (`.jdx`/`.dx`) |
| `tests/` | pytest coverage for ingest / JCAMP / peaks / baseline / UI helpers |

## Docs

- `PROJECT_TRUTH.md` — goal and feelings we protect
- `SPEC.md` — Phase 0 product surface
- `ROADMAP.md` — phases
- `STATUS.md` — Implemented vs Planned (honest)
- `AGENTS.md` — hard rules for agents and humans

## Non-goals (Phase 0 / MVP)

Hardware drivers, NMR/FID, RTL-SDR, compound libraries / ID claims.
JCAMP-DX basic ingest is Implemented (MIT `jcamp`); advanced JCAMP features remain Planned.
