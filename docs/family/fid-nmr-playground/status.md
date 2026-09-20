# Status — FID / NMR Playground

**As of:** 2026-09-19 (PT)  
**Phase:** 0 — software stub Implemented (mock/synthetic)  
**Blocked on:** licensed FID fixtures, Chemistry teaching-example picks, UI mode

## Done

- Doc pack drafted
- **Phase 0 software stub** (`fidnmr/`):
  - `FID` complex container + metadata (`sw_hz`, `obs_mhz`, `ref_ppm`, nucleus)
  - Exponential apodization; FFT; `phc0`/`phc1` phase
  - Hz or ppm axis → `spectrum_core.Spectrum` (`ppm` added to core XUnit)
  - Synthetic 1H-like mock FIDs + CLI `fidnmr-demo` / `python -m fidnmr.demo`
  - pytest (axis math, peak recovery, phase decorrelation, validation)

## Next

1. Chemistry: 1H teaching targets  
2. Collect fixture URLs/licenses (≥2 public FIDs)  
3. UI mode (time + spectrum views)  
4. Teaching note (Chemistry-reviewed)

## Claim hygiene

- Software stub is *Implemented* (synthetic / unit-tested only).
- Licensed fixtures, live spectrometer drivers, UI, and compound ID remain *Planned* / out of scope.
- Never claim structure elucidation or clinical NMR from this stub.
