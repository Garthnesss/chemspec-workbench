# Project Truth — ChemSpec Workbench

## One-sentence goal

A **software-only** workbench for real UV-Vis / IR (Raman optional) spectra with
SDR-style plot / waterfall / peaks — honest tools, **no magic compound ID**.

## Feelings we protect

- Immediate file → plot
- Honest units and labels
- Shared `spectrum_core` reusable by TeachSpec / FID-NMR / LabRF later
- Never market Planned as Done
- Chemistry-reviewed labels before any “real compound” examples

## Done means (Phase 0 exit)

CSV open, zoomable spectrum, peak table, one baseline method, overlay + folder
waterfall, fixtures + tests, truth/agents files.

## Claim classes

| Claim | Class |
|-------|--------|
| Opens fixture CSV and loads Spectrum | Implemented (tests) |
| Peak picker on fixtures | Implemented (tests) |
| Polynomial baseline on fixtures | Implemented (tests) |
| CLI / matplotlib demo | Implemented |
| Matches vendor instrument X | Deferred |
| Compound ID / library search | Deferred — never oversell |
| Live USB spectrometer | Deferred → TeachSpec |
