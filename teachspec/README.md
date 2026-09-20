# TeachSpec (Phase 0 software stub)

Educational optical teaching spectrometer **software** path for the Spectrum Family.

**v1 sensor lock (docs):** USB camera (UVC) is the **primary** sensor. Linear CCD/CMOS is a Planned alternate / Phase 2+.  
**Honesty:** Phase-0 code is still **mock-only** — no live UVC/camera driver is Implemented.

## What this package does (now)

- Pixel → nm **linear** (and optional **quadratic**) calibration from ≥2 known lines
- Save / load calibration JSON
- `OpticalLiveFrame` (1-D intensity + meta) → `spectrum_core.Spectrum` after calibration
- Synthetic CFL-like mock frames for demos and pytest (**no camera libraries**)
- UVC ingest **interface stub**: `OpticalFrameSource` protocol + `UvcIngestStub` (raises `NotImplementedError`) + pure-NumPy `extract_row` — see `teachspec/uvc_ingest.py`

## What this package does **not** do yet

- Live UVC ingest / OpenCV capture (interface stub only — `UvcIngestStub.read_frame` raises; **not Implemented**)
- Priced / vendor-locked BOM (skeleton in `docs/family/teachspec/BOM_v0.md`)
- Compound identification
- Hardware-verified wavelength claims (teaching-calibrated only)

## Quick try

After `pip install -e ".[dev]"` (or editable install of the workbench):

```bash
# console script (same entry as below)
teachspec-demo

# or module form
python -m teachspec.demo

# optional knobs
teachspec-demo --n-pixels 512 --prominence 0.2

# unit tests (no hardware)
pytest -q tests/test_teachspec.py
```

Expected output: a short peak table from a **synthetic** CFL-like mock frame, plus an
explicit disclaimer that this is not a hardware capture and not compound ID.

## Docs

| Doc | Role |
|-----|------|
| `docs/family/teachspec/SPEC.md` | Locked hardware/software target (USB-cam primary) |
| `docs/family/teachspec/SAFETY.md` | Classroom safety one-pager |
| `docs/family/teachspec/BOM_v0.md` | USB-cam path BOM skeleton (TBD prices) |
| `docs/family/teachspec/roadmap.md` / `status.md` | Phase checklist / claim hygiene |
| `teachspec/uvc_ingest.py` | UVC protocol + NotImplemented stub (no OpenCV dep) |
