# Status — TeachSpec

**As of:** 2026-09-19 (PT)  
**Phase:** 0 — software stub Implemented; **USB camera (UVC) locked as v1 primary sensor**  
**Blocked on:** classroom safety review (SAFETY.md drafted), BOM v0 pricing pass, live UVC driver

## Done

- Project Truth / SPEC / roadmap drafted (family docs)
- **Sensor lock:** USB camera (UVC) = v1 primary; linear CCD/CMOS = Planned alternate / Phase 2+
- **Phase 0 software stub** (`teachspec/`):
  - pixel→nm linear + optional quadratic calibration; JSON save/load
  - `OpticalLiveFrame` → `spectrum_core.Spectrum` (calibrated path)
  - synthetic CFL-like mock frames + CLI demo (`teachspec-demo` / `python -m teachspec.demo`)
  - pytest (fit correctness, bad inputs, mock→Spectrum roundtrip, cal I/O)
  - UVC ingest **interface stub** (`teachspec/uvc_ingest.py`): `OpticalFrameSource` + `UvcIngestStub` → `NotImplementedError`; `extract_row` NumPy helper (no OpenCV dep)

## In progress / drafting

- `SAFETY.md` classroom one-pager drafted (human teacher-facing sign-off still open)
- `BOM_v0.md` skeleton for USB-cam path (placeholder line items; TBD price ranges)

## Next (human / Planned)

1. Safety review of SAFETY.md (teacher-facing sign-off)
2. BOM v0 price pass + first optical bench spike
3. Live UVC ingest: camera frame → 1-D row → `OpticalLiveFrame` (**interface stub only**; live driver not Started; Phase-0 remains mock-only)
4. Linear CCD/CMOS alternate deferred to Phase 2+

## Claim hygiene

- Software stub is *Implemented* (synthetic / unit-tested only).
- Sensor **choice** is locked in docs; UVC **interface** stub is importable but live driver, priced BOM, and hardware-verified calibration remain *Planned* / drafting.
- Never claim compound ID, clinical use, or lab-grade / metrology wavelength accuracy from this stub.
