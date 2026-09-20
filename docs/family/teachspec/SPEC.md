# TeachSpec v1 — Locked Spec (Phase 0 design)

**Depends on:** `spectrum-core` + ChemSpec UI patterns  
**Status:** Phase-0 software stub Implemented (mock/calibration); optional live UVC OpenCV ingest Implemented as `[teachspec]` extra; hardware bench still in progress (sensor locked; safety + BOM drafting)

## Hardware (v1 target)

| Item | Spec |
|------|------|
| Disperser | Transmission diffraction grating (e.g. 1000 lines/mm class) or DVD-grating teaching variant (document which in BOM) |
| Sensor | **USB camera (UVC) — primary for v1** (locked). Linear CCD/CMOS module = Planned alternate / Phase 2+ |
| Slit | Fixed mechanical slit |
| Source | Visible lamp + optional known-line calibrator (prefer CFL / neon teaching lamps; see SAFETY.md) |
| Host | Laptop via USB; ESP32 optional later for tethered mode |

## Software

- Ingest adapter: `OpticalLiveFrame` → `Spectrum` (intensity vs pixel → vs nm after calibration)
- **UVC ingest interface:** `teachspec.uvc_ingest` — `OpticalFrameSource` + `extract_row` + `UvcIngestStub` (explicit no-camera placeholder)
- **Live UVC OpenCV path (Implemented, optional extra):** `UvcOpenCvSource` / `open_uvc_source()` via `opencv-python-headless` (`pip install -e ".[teachspec]"`); CI/default remain camera-free. Frames are intensity vs pixel until `teachspec.calibration`; not wavelength-calibrated by the camera alone. Live use subject to SAFETY.md
- Calibration: user clicks ≥2 known lines → linear (then quadratic) fit; store calibration file
- Reuse ChemSpec: plot, peak pick, baseline, export CSV
- Claim class: *hardware-verified* only after named BOM + calibration log

## Non-goals v1

Auto compound ID, UV-C / germicidal systems, motorized scanning monochromators, clinical or regulated diagnostics, metrology-grade wavelength claims.

## Deliverables

1. BOM + wiring/optics diagram (BOM_v0 skeleton drafted; priced vendor lock later)
2. `teachspec` ingest package + calibration routine (mock path Implemented)
3. Build/calibrate checklist in README
4. Unit tests for pixel→nm fit math (fixtures, no camera required)
5. Classroom SAFETY.md one-pager
