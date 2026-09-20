# Status — TeachSpec

**As of:** 2026-09-19 (PT)  
**Phase:** 0 — software stub Implemented; **USB camera (UVC) locked as v1 primary sensor**; optional live OpenCV UVC path Implemented  
**Blocked on:** classroom safety review (SAFETY.md drafted), BOM v0 pricing pass, bench optical path

## Done

- Project Truth / SPEC / roadmap drafted (family docs)
- **Sensor lock:** USB camera (UVC) = v1 primary; linear CCD/CMOS = Planned alternate / Phase 2+
- **Phase 0 software stub** (`teachspec/`):
  - pixel→nm linear + optional quadratic calibration; JSON save/load
  - `OpticalLiveFrame` → `spectrum_core.Spectrum` (calibrated path)
  - synthetic CFL-like mock frames + CLI demo (`teachspec-demo` / `python -m teachspec.demo`; default `--mock`)
  - pytest (fit correctness, bad inputs, mock→Spectrum roundtrip, cal I/O)
  - UVC ingest contract (`teachspec/uvc_ingest.py`): `OpticalFrameSource` + `UvcIngestStub` + `extract_row`
  - **Live UVC OpenCV path (optional extra):** `UvcOpenCvSource` / `open_uvc_source()`; `pip install -e ".[teachspec]"`; CI stays camera-free (OpenCV mocked in tests); `--live` CLI flag

## In progress / drafting

- `SAFETY.md` classroom one-pager drafted (human teacher-facing sign-off still open)
- `BOM_v0.md` skeleton for USB-cam path (placeholder line items; TBD price ranges)

## Next (human / Planned)

1. Safety review of SAFETY.md (teacher-facing sign-off)
2. BOM v0 price pass + first optical bench spike
3. NiceGUI live view / auto-cal from CFL (out of scope for the OpenCV ingest PR)
4. Linear CCD/CMOS alternate deferred to Phase 2+

## Claim hygiene

- Software stub is *Implemented* (synthetic / unit-tested).
- Optional live UVC OpenCV ingest is *Implemented* as an extra — **not** a core dependency; frames are intensity vs pixel until user calibration; not compound ID; not hardware-verified wavelength by camera alone.
- Sensor **choice** is locked in docs; priced BOM and hardware-verified calibration remain *Planned* / drafting.
- Never claim compound ID, clinical use, or lab-grade / metrology wavelength accuracy from this stub.
