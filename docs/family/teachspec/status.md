# Status — TeachSpec

**As of:** 2026-09-19 (PT)  
**Phase:** 0 — software stub Implemented; hardware design still open  
**Blocked on:** sensor choice (USB-cam vs linear CCD), Chemistry safety review, BOM

## Done

- Project Truth / SPEC / roadmap drafted (family docs)
- **Phase 0 software stub** (`teachspec/`):
  - pixel→nm linear + optional quadratic calibration; JSON save/load
  - `OpticalLiveFrame` → `spectrum_core.Spectrum` (calibrated path)
  - synthetic CFL-like mock frames + CLI demo (`python -m teachspec.demo`)
  - pytest (fit correctness, bad inputs, mock→Spectrum roundtrip, cal I/O)

## In progress

- Nothing hardware yet

## Next (human / Planned)

1. Chemistry: classroom constraints + safety notes  
2. Pick USB-cam vs linear sensor (no lock in software yet)  
3. BOM v0 + first optical bench spike after sensor choice  
4. Live camera / CCD ingest (not Started)

## Claim hygiene

- Software stub is *Implemented* (synthetic / unit-tested only).
- Sensor choice, BOM, live camera, and hardware-verified calibration remain *Planned*.
- Never claim compound ID or lab-grade accuracy from this stub.
