# Roadmap — TeachSpec

| Phase | Name | Status | Outcome |
|-------|------|--------|---------|
| 0 | Design lock + software stub | **Software stub Implemented**; sensor locked; optional live UVC OpenCV Implemented | Truth + SPEC + `teachspec/` mock/calibration + optional OpenCV UVC; USB-cam primary locked; SAFETY + BOM_v0 drafting |
| 1 | Bench prototype | Planned | One working optical path + live UVC → plot / NiceGUI |
| 2 | Calibration UX | Planned | Known-line fit UI + saved calibration in ChemSpec-style UI |
| 3 | Enclosure + guide | Planned | Reproducible classroom build |
| 4 | Kit polish | Goal | Meets Project Truth “done” table |

## Phase 0 checklist

- [x] Project Truth
- [x] SPEC draft
- [x] Software stub: calibration + OpticalLiveFrame → Spectrum + mock source + tests
- [x] Choose primary sensor — **USB camera (UVC)** for v1; linear CCD/CMOS = Phase 2+ alternate
- [ ] Chemistry / classroom safety review (SAFETY.md drafting — next human gate)
- [ ] BOM v0 priced skeleton (USB-cam path)
- [x] UVC ingest **interface stub** (`OpticalFrameSource` + `UvcIngestStub` → NotImplementedError; no OpenCV dep)
- [x] Live UVC OpenCV path (`UvcOpenCvSource` / `open_uvc_source`; optional `[teachspec]` extra) — Implemented; CI camera-free; intensity vs pixel until calibration
- [x] Gate: ChemSpec `spectrum-core` plot/peak stable (reuse Implemented)

## Exit Phase 0 (full)

Sensor choice locked ✓; optional live UVC OpenCV path Implemented ✓; BOM v0 priced; Chemistry safety notes reviewed. Software stub + optional driver do **not** exit the hardware half of Phase 0 (bench + priced BOM still open).
