# Status — FID / NMR Playground

**As of:** 2026-09-20 (PT)  
**Phase:** 0 — software stub Implemented (mock/synthetic); mock NiceGUI UI Implemented  
**Blocked on:** licensed FID fixtures, Chemistry teaching-example picks

## Done

- Doc pack drafted
- **Phase 0 software stub** (`fidnmr/`):
  - `FID` complex container + metadata (`sw_hz`, `obs_mhz`, `ref_ppm`, nucleus)
  - Exponential apodization; FFT; `phc0`/`phc1` phase
  - Hz or ppm axis → `spectrum_core.Spectrum` (`ppm` added to core XUnit)
  - Synthetic 1H-like mock FIDs + CLI `fidnmr-demo` / `python -m fidnmr.demo`
  - pytest (axis math, peak recovery, phase decorrelation, validation)
  - Thin examples twin: `examples/fidnmr_walkthrough.py` + pytest smoke (no notebook yet)
  - **NiceGUI playground:** `fidnmr-ui` / `python -m fidnmr.ui_app` (port 8083); mock time + spectrum

## Next

1. Chemistry: 1H teaching targets  
2. Collect fixture URLs/licenses (≥2 public FIDs)  
3. Teaching note (Chemistry-reviewed)

## Claim hygiene

- Software stub + mock UI are *Implemented* (synthetic / unit-tested only).
- Licensed fixtures, live spectrometer drivers, and compound ID remain *Planned* / out of scope.
- Never claim structure elucidation or clinical NMR from this stub.
