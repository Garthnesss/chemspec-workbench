# ChemSpec Workbench (+ LabRF Monitor)

Software-only workbench for **UV-Vis / IR** spectra: open CSV, plot, find peaks
(center, height, prominence, **FWHM**, **area**), correct a simple baseline,
overlay/stack traces, export peaks, A↔%T display, folder waterfall, and
**analysis session** save/load (`.csw.json`). Built on a
reusable `spectrum_core` package (Spectrum Family).

Sibling app **LabRF Monitor** (`labrf/`): receive-only RF power spectrum + waterfall
from **mock IQ** (CI/UI default) or optional RTL-SDR. Educational EMI awareness —
**not** chemical ID, **not** regulatory advice, **no transmit**.

**Honesty:** ChemSpec does **not** identify compounds or drive spectrometers.
LabRF mock mode does **not** claim live RF until STATUS says hardware-verified.
Synthetic fixtures are labeled as synthetic; public NIST/PNNL IR fixtures (Owner: Public domain) live in `fixtures/public/` with attribution in `SOURCES.md` — still no compound-ID claims.

## Install / Developer setup

Fresh checkout (matches CI — includes `jcamp` from main deps plus pytest / UI / baselines):

```bash
cd chemspec-workbench
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,ui,baselines]"
pytest -q
```

Or mirror CI with Make / script:

```bash
make test
# or: ./scripts/ci-test.sh
```

Minimal install (core + pytest only):

```bash
pip install -e ".[dev]"
```

Optional extras:

```bash
pip install -e ".[baselines]"          # pybaselines (BSD-3); also in [dev]
pip install -e ".[ui]"                 # NiceGUI + Plotly
pip install -e ".[ui,baselines]"
pip install -e ".[labrf]"              # optional pyrtlsdr (hardware not required for CI)
```

`jcamp` is a **required** dependency (not optional) so JCAMP ingest and public IR fixture tests work after a clean install.

## ChemSpec interactive UI (NiceGUI)

```bash
pip install -e ".[ui]"
python -m chemspec.ui_app
# or: chemspec-ui
```

Then open **http://localhost:8080**.

## LabRF Monitor (mock IQ UI — no dongle)

```bash
pip install -e ".[ui]"
python -m labrf.ui_app
# or: python -m labrf
# or: labrf-ui
```

Then open **http://localhost:8081**.

**Demo tips (showable without hardware):**

1. Click **Start stream** — spectrum + waterfall update continuously from synthetic IQ.
2. Use **quick preset** buttons (FM / ISM / …) to jump center/span.
3. Set a **power threshold (dB)**; events appear in the log when peaks/max bin exceed it;
   **Export events CSV** / **Clear events** as needed.
4. **Load mock fixture** for a one-click synthetic capture from `fixtures/labrf/mock_iq.npz`.
5. Provenance line shows source (mock/fixture), center, rate, frames, streaming mode.

- Educational presets with disclaimer banner (not regulatory advice)
- Live RTL-SDR only if `pip install -e ".[labrf]"` **and** a dongle is present
  (not required for tests or the mock UI)

## Test

```bash
pip install -e ".[dev,ui,baselines]"   # same extras as CI
pytest -q
# or: make test
```

ChemSpec tests (CSV/JCAMP/public fixtures) and LabRF mock tests (no dongle) should both pass.
GitHub Actions (`.github/workflows/ci.yml`) runs the same install + `pytest -q` on Python 3.11 and 3.13 for every push/PR to `main`.

## Run ChemSpec demos (no UI)

```bash
python -m chemspec.demo
python chemspec/plot_demo.py --fixture ir --save ir_demo.png --no-show
```


## Analysis sessions

Save a reproducible analysis snapshot from the NiceGUI UI (**2b · Analysis session**)
or from Python:

```python
from spectrum_core import ingest, find_peaks, save_session, load_session

spec = ingest("sample.csv")
peaks = find_peaks(spec, prominence=0.15)
save_session(
    "analysis.csw.json",
    spec,
    processing={"baseline_on": True, "baseline_method": "polynomial", "baseline_degree": 1},
    peaks=peaks,
    notes="optional lab notes",
    source_path="sample.csv",
)
session = load_session("analysis.csw.json")  # embedded x/y — path may have moved
```

File extensions: `.csw.json` or `.chemspec.json`. Schema is documented in `SPEC.md`
(`format_version`, embedded spectrum, processing, peaks, notes, provenance).
Sessions are analysis snapshots — **not** compound identification.

## Layout

| Path | Role |
|------|------|
| `spectrum_core/` | Shared Spectrum model (optical + RF units), CSV/JCAMP ingest, peaks (FWHM/area), baseline, overlay/stack, folder waterfall, **session save/load** |
| `chemspec/` | UV-Vis/IR demos + NiceGUI MVP |
| `labrf/` | LabRF Monitor: mock IQ, FFT→spectrum, stream generator, threshold events, waterfall, presets, optional RTL-SDR stub, NiceGUI UI |
| `fixtures/` | Synthetic UV-Vis/IR + `public/` (NIST/PNNL IR) + `waterfall/` + `labrf/mock_iq.npz` |
| `tests/` | pytest (ChemSpec + LabRF mock; no hardware) |
| `docs/family/` | Per-app Truth / SPEC / roadmap / status |

## Docs

- `PROJECT_TRUTH.md` / `SPEC.md` / `ROADMAP.md` / `STATUS.md` — ChemSpec
- `docs/family/labrf-monitor/` — LabRF Truth / SPEC / roadmap / status
- `AGENTS.md` — hard rules (incl. receive-only LabRF, no chem ID, educational presets)

## Non-goals

Hardware drivers for ChemSpec; compound libraries / ID claims; LabRF demodulation, TX,
compliance certification, or chemical ID via RF.
