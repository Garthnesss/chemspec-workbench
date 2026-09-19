# FID / NMR Playground v1 — Locked Spec (Phase 0 design)

**Depends on:** `spectrum-core` (complex series + FFT helpers)  
**Status:** Planned

## Data

- Input: FID as complex64 (or interleaved float) + metadata JSON: `sw_hz`, `obs_mhz`, `npts`, `ref_ppm`, nucleus  
- Fixtures: ≥2 public-domain or clearly licensed 1H FIDs (document source URLs/licenses in `fixtures/SOURCES.md`)

## Processing pipeline (explicit UI steps)

1. Display FID (real/imag or magnitude)  
2. Optional apodization (exp line broadening)  
3. FFT → complex spectrum  
4. Phase: `phc0`, `phc1` sliders  
5. Axis: Hz and ppm using `obs_mhz` + `ref_ppm`  
6. Peak pick (reuse core) + table export

## Non-goals v1

Live Bruker/Varian driver, automated structure ID, 2D spectra.

## Deliverables

1. `fid_ingest` + FFT/phase functions with unit tests  
2. UI page or mode inside family app shell  
3. Fixture pack + SOURCES.md  
4. Short “how to read this” teaching note (Chemistry-reviewed)
