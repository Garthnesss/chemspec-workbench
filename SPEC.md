# ChemSpec Workbench v1 — Spec (Phase 0)

## Core package: `spectrum_core`

| Module | Responsibility |
|--------|----------------|
| `Spectrum` | x (nm \| cm⁻¹), y (A \| %T \| intensity), title/meta |
| `ingest_csv` | CSV primary; column index or header name |
| `ingest_jcamp` | JCAMP-DX basic via MIT `jcamp.readfile`; unit mapping from headers |
| `ingest` | Suffix dispatch (`.jdx`/`.dx` → JCAMP; else CSV) |
| `find_peaks` | `scipy.signal.find_peaks`, configurable prominence |
| `baseline_polynomial` | poly fit / subtract (always available) |
| `baseline_correct` | dispatch: polynomial default; optional pybaselines `asls` / `mpls` (`[baselines]`, BSD-3) |
| `overlay` / `stack` | multi-spectrum helpers |
| `units` | A ↔ %T pure conversion (`convert_spectrum_y`); intensity blocked |
| `export_peaks` | `peaks_to_csv` peak table serialization |
| `folder` | `ingest_folder` / `folder_waterfall` (CSV+JCAMP → stack) |
| JCAMP advanced | Planned (multi-block / certification) |

## ChemSpec layer

- CLI demo: peak table for synthetic fixtures (`python -m chemspec.demo`)
- Matplotlib plot demo: `chemspec/plot_demo.py`
- NiceGUI + Plotly MVP: optional `[ui]` extra (`python -m chemspec.ui_app`); core demos run without it
  - Peak CSV download, A↔%T display toggle, folder waterfall
  - Baseline method picker (polynomial + optional AsLS/MPLS)

## Primary format

CSV with column mapping (primary). JCAMP-DX basic (`.jdx`/`.dx`) via MIT `jcamp`.
Fixtures: synthetic UV-Vis + IR (CSV and JCAMP) + `fixtures/waterfall/` stack demo.

## Non-goals

Hardware, compound libraries, NMR/FID, RTL-SDR, clinical claims, SaaS.
Baseline tools correct continuum only — **no compound-ID claims**.
