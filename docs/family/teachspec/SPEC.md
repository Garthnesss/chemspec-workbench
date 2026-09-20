# TeachSpec v1 — Locked Spec (Phase 0 design)

**Depends on:** `spectrum-core` + ChemSpec UI patterns  
**Status:** Phase-0 software stub Implemented (mock/calibration); hardware design still Planned

## Hardware (v1 target)

| Item | Spec |
|------|------|
| Disperser | Transmission diffraction grating (e.g. 1000 lines/mm class) or DVD-grating teaching variant (document which) |
| Sensor | USB camera *or* linear CCD/CMOS module (pick one primary in Phase 1 scaffold) |
| Slit | Fixed mechanical slit |
| Source | Visible lamp + optional known-line calibrator (CFL / Hg teaching lamp) |
| Host | Laptop via USB; ESP32 optional later for tethered mode |

## Software

- Ingest adapter: `OpticalLiveFrame` → `Spectrum` (intensity vs pixel → vs nm after calibration)
- Calibration: user clicks ≥2 known lines → linear (then quadratic) fit; store calibration file
- Reuse ChemSpec: plot, peak pick, baseline, export CSV
- Claim class: *hardware-verified* only after named BOM + calibration log

## Non-goals v1

Auto compound ID, UV-C deep-UV systems without safety review, motorized scanning monochromators.

## Deliverables

1. BOM + wiring/optics diagram  
2. `teachspec` ingest package + calibration routine  
3. Build/calibrate checklist in README  
4. Unit tests for pixel→nm fit math (fixtures, no camera required)
