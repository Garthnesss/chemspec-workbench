# Status — TeachSpec

**As of:** 2026-09-20 (PT)  
**Phase:** 0 — software stub Implemented; **USB camera (UVC) locked as v1 primary sensor**; optional live OpenCV UVC + NiceGUI preview Implemented  
**Blocked on:** classroom safety review (SAFETY.md drafted), BOM purchasable-class / dated quotes, bench optical path; ChemSpec 0.2.0 PyPI publish waits on credentials

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
  - **NiceGUI live preview:** `teachspec-ui` / `python -m teachspec.ui_app` (needs `[ui]`; Live also `[teachspec]`); Mock default; intensity vs pixel; no CFL auto-cal

## In progress / drafting

- `SAFETY.md` classroom one-pager drafted (human teacher-facing sign-off still open)
- `BOM_v0.md` USB-cam path **purchasable classes** + approx USD ranges + search keywords (Amazon/Adafruit/Thorlabs-class; estimates change; no fake affiliate SKUs; DIY target <$75 excl. laptop)

## Next (human / Planned)

- Classroom pilot outreach using `docs/classroom_pilot_one_pager.md`

1. Safety review of SAFETY.md (teacher-facing sign-off)
2. BOM v0 price pass + first optical bench spike
3. CFL auto-cal / nm-axis in preview (NiceGUI intensity preview Implemented; auto-cal still Planned)
4. Linear CCD/CMOS alternate deferred to Phase 2+

## Claim hygiene

- Software stub is *Implemented* (synthetic / unit-tested).
- Optional live UVC OpenCV ingest is *Implemented* as an extra — **not** a core dependency; frames are intensity vs pixel until user calibration; not compound ID; not hardware-verified wavelength by camera alone.
- NiceGUI live preview (`teachspec-ui`) is *Implemented* — Mock default; Live optional; educational honesty banner; no compound ID.
- Sensor **choice** is locked in docs; priced BOM and hardware-verified calibration remain *Planned* / drafting.
- Never claim compound ID, clinical use, or lab-grade / metrology wavelength accuracy from this stub.
