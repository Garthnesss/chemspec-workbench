# ChemSpec Workbench — Phase 0 scope

**Status:** Planned (not Implemented)  
**Family:** Spectrum Core → ChemSpec first; FID/NMR + LabRF later  
**Process:** follow [AI shipping checklist](sand-workflow:ai-shipping-checklist)

---

## Goal (Phase 0)

Ship a **software-only** desktop or local web workbench that opens real UV-Vis / IR (and optionally Raman) spectra from files, shows an SDR-style spectrum + optional time waterfall, and runs honest peak/baseline tools — with a shared library we can reuse for later family projects.

## Non-goals (Phase 0)

- No “identify any unknown compound” marketing
- No hardware spectrometer drivers yet (TeachSpec is a later project)
- No NMR/FID or RTL-SDR ingest yet (adapters stubbed only)
- No cloud account / SaaS
- No clinical or regulated diagnostic claims

## Users

1. Students learning how to read a spectrum  
2. You / Chemistry — validating formats and pedagogy  
3. Later: lab techs doing quick looks at exported instrument CSVs

## Shared core (extract from day one)

Package `spectrum-core` (name TBD):

| Module | Responsibility |
|--------|----------------|
| `Spectrum` | x-axis (nm / cm⁻¹ / eV), y-axis (A / %T / intensity), units metadata |
| `PeakPicker` | prominence/threshold peak detect + labels |
| `Baseline` | simple polynomial or ALS-style baseline (start simple) |
| `Waterfall` | stack of spectra over time / batch |
| `Ingest` | adapters: CSV, JCAMP-DX (nice-to-have), stub for FID / RTL later |

ChemSpec Workbench = UI + chem-specific presets on top of this core.

## MVP features (Phase 0 exit)

- [ ] Open CSV spectrum (wavelength/wavenumber + intensity columns; user maps columns if needed)
- [ ] Plot spectrum (zoom/pan); toggle absorbance ↔ transmittance helper if data allows
- [ ] Peak detect with adjustable sensitivity; export peak table
- [ ] Baseline correct (one solid method)
- [ ] Overlay 2–N spectra (batch folder or multi-file)
- [ ] Optional waterfall for a folder of time-stamped spectra
- [ ] `PROJECT_TRUTH.md` + `.agents.md` + host unit tests for peak/baseline/ingest
- [ ] Example datasets in-repo (public domain / synthetic) so demos work offline

## Claim classes

| Claim | Class |
|-------|--------|
| Opens fixture CSV and plots | Implemented (tests) |
| Peak picker on fixtures | Implemented (tests) |
| Matches vendor instrument X | Deferred until Chemistry confirms formats |
| Compound ID / library search | Deferred (Phase 1+; never oversell) |
| Live USB spectrometer | Deferred → TeachSpec |

## Suggested stack (decide at scaffold)

- **Fast path:** Python + scipy/numpy + a small UI (NiceGUI / Streamlit / local FastAPI + canvas) — best for chem file ecosystem  
- **Alt:** TypeScript core + web canvas — better if LabRF/web viz kinship matters more  

Default recommendation: **Python first** (chem culture + JCAMP later), keep `spectrum-core` API clean enough to reimplement viz in TS later if needed.

## File formats (Phase 0)

1. **CSV** — primary (column mapping UI)  
2. **JCAMP-DX** — stretch goal if Chemistry says it’s the lab lingua franca  
3. Fixtures: at least one UV-Vis and one IR example

## Phase 0 success criteria

1. Cold start → open example IR → see peaks labeled in &lt; 1 minute  
2. Unit tests cover ingest + peak/baseline on fixtures (CI green)  
3. Truth file lists only verified behaviors  
4. Chemistry sign-off: “formats and labels aren’t chemically misleading”

## Next phases (not now)

- **Phase 1:** reference peak libraries (limited, cited), simple similarity score with uncertainty  
- **FID/NMR Playground:** FID ingest adapter on same core  
- **LabRF Monitor:** RTL-SDR adapter + EMI presets  
- **TeachSpec:** optical hardware path  

## Human gates

- Product direction, “what we claim,” release tags — JARTH  
- Chemical honesty of labels/units/examples — Chemistry  
- Scaffold/implement — Erik (+ checklist)

## Immediate next actions

1. Chemistry: confirm priority formats + 2–3 public example files  
2. Scaffold repo: `spectrum-core` + `chemspec-workbench` + truth/agents files  
3. First failing tests: CSV ingest + peak pick on fixture  
