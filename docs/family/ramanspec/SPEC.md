# RamanSpec v0 — Pivot SPEC (library-assist)

**Status:** Draft sketch only — **not Implemented**  
**Depends on:** `spectrum_core` (Spectrum, peaks contract, processing, sessions)  
**Sibling of:** ChemSpec (primary), TeachSpec, LabRF, FID-NMR  

## Positioning

```
ChemSpec Workbench     = UV-Vis / IR teaching + reproducible analysis   [PRIMARY]
RamanSpec (optional)   = Raman / probe library-ASSIST                   [PIVOT]
```

RamanSpec is a **thin application** on `spectrum_core`, not a rewrite.

## Data model

- `x_unit`: Raman shift `cm-1` (required for library search)
- `y_unit`: `intensity` (default); never pretend calibrated absolute Raman cross-section unless documented
- Reuse `Peak` measurement contract (prominence-relative FWHM/area) — same honesty as ChemSpec 0.2
- Sessions: `format_version` ≥ 2 with `raw_data_hash` + fingerprint including **library id + search params** (not timestamps)

## Library-assist (not ID)

### Inputs
- Query spectrum (processed or raw — record which in history)
- Library: list of reference spectra with license metadata (e.g. teaching polymer pack; RRUFF-like open data only when license allows redistribution)

### Algorithm (v0)
1. Optional preprocess: baseline (asymmetric least squares or polynomial), snip fluorescence, normalize (max or area)
2. Interpolate query + references onto shared cm⁻¹ grid
3. Score: cosine similarity on intensity vectors (document alternatives: correlation, hit-quality index later)
4. Return **top-k** (`k` default 5) with score ∈ [0, 1], reference id, license note

### Required UI / export copy
- Banner: **“Library candidates — not compound identification.”**
- Each hit: name/id, score, “match quality: exploratory”
- Export CSV/JSON must include disclaimer field
- Forbidden: single “Identity = X” badge without user override labeled *manual assignment*

## Ingest adapters (phased)

| Phase | Adapter | Claim |
|-------|---------|-------|
| 0 | CSV / JCAMP-DX Raman files | Software-only |
| 1 | One USB spectrometer SDK (TBD vendor) | Hardware optional; not “validated method” |
| 2 | TeachSpec-like cheap Raman teaching kit | Laser SAFETY.md mandatory |

## Safety / compliance

- Any live laser path requires `docs/family/ramanspec/SAFETY.md` (laser class, eyewear, beam path) before shipping UI that enables laser
- No medical or controlled-substance workflows in v0

## Non-goals v0

- Deep learning end-to-end ID
- Mixture deconvolution as a product claim
- Replacing ChemSpec as the default README headline

## Success metrics (teaching / portfolio)

- Student can explain why #1 hit scored high and when to distrust it
- Session replay reproduces the same top-k given same library version
- Public demo never utters “identified”

## Implementation sketch (when greenlit)

1. `ramanspec/` package: `library.py`, `search.py`, `ingest_raman.py`
2. `tests/fixtures/raman/` synthetic peaks + tiny fake library
3. Optional ChemSpec UI tab or `ramanspec-ui` — only after ChemSpec stays primary in README
4. Library version pin in session fingerprint

## Decision gate (human)

Do we want RamanSpec as:
- **A.** Teaching library-assist only, or  
- **B.** Narrow vertical (e.g. plastics) with curated library, still non-ID UX?

Either is compatible with this SPEC; “universal chemical ID” is not.
