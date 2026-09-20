# FID / NMR Playground v1 — Locked Spec (Phase 0 design)

**Depends on:** `spectrum-core` (Spectrum + peaks; `ppm` / `Hz` x units)  
**Status:** Phase-0 software stub Implemented (mock FID + FFT/phase); fixtures / UI still Planned

## Data

- Input: FID as complex64 (or interleaved float) + metadata: `sw_hz`, `obs_mhz`, `npts`, `ref_ppm`, nucleus  
- Phase 0: synthetic mock FIDs (`fidnmr.mock_source`) — labeled synthetic  
- Later: ≥2 public-domain or clearly licensed 1H FIDs (document source URLs/licenses in `fixtures/SOURCES.md`)

## Processing pipeline (explicit steps)

1. Display FID (real/imag or magnitude) — math ready; UI Planned  
2. Optional apodization (exp line broadening) — Implemented in stub  
3. FFT → complex spectrum — Implemented  
4. Phase: `phc0`, `phc1` — Implemented (headless)  
5. Axis: Hz and ppm using `obs_mhz` + `ref_ppm` — Implemented  
6. Peak pick (reuse core) + table export — core reuse via demo/tests  

## Non-goals v1

Live Bruker/Varian driver, automated structure ID / compound ID, 2D spectra, clinical claims.

## Deliverables

1. `fidnmr` package: FID + FFT/phase + mock source + unit tests — **Phase 0 Implemented**  
2. UI page or mode inside family app shell — Planned  
3. Fixture pack + SOURCES.md — Planned  
4. Short “how to read this” teaching note (Chemistry-reviewed) — Planned  
