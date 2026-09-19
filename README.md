# ChemSpec Workbench

Software-only workbench for **UV-Vis / IR** spectra: open CSV, plot, find peaks,
correct a simple baseline, overlay/stack traces. Built on a reusable
`spectrum_core` package (Spectrum Family).

**Honesty:** Phase 0 does **not** identify compounds, drive spectrometers, or
read NMR/FID/RTL-SDR. Synthetic fixtures are labeled as synthetic.

## Install

```bash
cd chemspec-workbench
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Optional UI extras (NiceGUI / Streamlit) when you want them:

```bash
pip install -e ".[dev,ui]"
```

## Test

```bash
pytest
```

## Run demos

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
| `spectrum_core/` | Shared Spectrum model, CSV ingest, peaks, baseline, overlay/stack |
| `chemspec/` | ChemSpec demos (`demo`, `plot_demo`) |
| `fixtures/` | Synthetic UV-Vis + IR CSVs |
| `tests/` | pytest coverage for ingest / peaks / baseline |

## Docs

- `PROJECT_TRUTH.md` — goal and feelings we protect  
- `SPEC.md` — Phase 0 product surface  
- `ROADMAP.md` — phases  
- `STATUS.md` — Implemented vs Planned (honest)  
- `AGENTS.md` — hard rules for agents and humans  

## Non-goals (Phase 0)

Hardware drivers, JCAMP (stub only), NMR/FID, RTL-SDR, compound libraries / ID claims.
