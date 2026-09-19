# ChemSpec Workbench v1 — Spec (Phase 0)

## Core package: `spectrum_core`

| Module | Responsibility |
|--------|----------------|
| `Spectrum` | x (nm \| cm⁻¹), y (A \| %T \| intensity), title/meta |
| `ingest_csv` | CSV primary; column index or header name |
| `find_peaks` | `scipy.signal.find_peaks`, configurable prominence |
| `baseline_polynomial` | poly fit / subtract |
| `overlay` / `stack` | multi-spectrum helpers |
| JCAMP | stub (`NotImplementedError`) only |

## ChemSpec layer

- CLI demo: peak table for synthetic fixtures (`python -m chemspec.demo`)
- Matplotlib plot demo: `chemspec/plot_demo.py`
- NiceGUI + Plotly MVP: optional `[ui]` extra (`python -m chemspec.ui_app`); core demos run without it

## Primary format

CSV with column mapping. Fixtures: synthetic UV-Vis + IR.

## Non-goals

Hardware, compound libraries, NMR/FID, RTL-SDR, clinical claims, SaaS.
