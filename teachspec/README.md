# TeachSpec (Phase 0 software stub + optional live UVC)

Educational optical teaching spectrometer **software** path for the Spectrum Family.

**v1 sensor lock (docs):** USB camera (UVC) is the **primary** sensor. Linear CCD/CMOS is a Planned alternate / Phase 2+.  
**Honesty:** Default installs stay **camera-free** (mock + calibration). Live OpenCV UVC is an **optional** `[teachspec]` extra — intensity vs pixel until you apply `teachspec.calibration`. Not compound ID; not hardware-verified wavelength by the camera alone. Live classroom use remains subject to `docs/family/teachspec/SAFETY.md`.

## What this package does (now)

- Pixel → nm **linear** (and optional **quadratic**) calibration from ≥2 known lines
- Save / load calibration JSON
- `OpticalLiveFrame` (1-D intensity + meta) → `spectrum_core.Spectrum` after calibration
- Synthetic CFL-like mock frames for demos and pytest (**no camera libraries**)
- UVC ingest contract: `OpticalFrameSource` + pure-NumPy `extract_row` + `UvcIngestStub` (explicit no-camera placeholder)
- **Live UVC OpenCV path (optional):** `UvcOpenCvSource` / `open_uvc_source()` via `opencv-python-headless` (`pip install -e ".[teachspec]"`)

## What this package does **not** do yet

- NiceGUI live camera view (can add later)
- Auto-calibration from a live CFL frame in the same CLI pass
- Priced / vendor-locked BOM (skeleton in `docs/family/teachspec/BOM_v0.md`)
- Compound identification
- Hardware-verified / metrology wavelength claims (teaching-calibrated only)

## Quick try

After `pip install -e ".[dev]"` (or editable install of the workbench):

```bash
# console script — default is mock (camera-free)
teachspec-demo
teachspec-demo --mock --n-pixels 512 --prominence 0.2

# live UVC (optional extra; needs a camera)
pip install -e ".[teachspec]"
teachspec-demo --live --device 0

# or module form
python -m teachspec.demo
python -m teachspec.demo --live --device 0

# unit tests (no hardware; OpenCV mocked)
pytest -q tests/test_teachspec.py tests/test_teachspec_uvc_ingest.py
```

Expected mock output: a short peak table from a **synthetic** CFL-like frame, plus an
explicit disclaimer that this is not a hardware capture and not compound ID.

Expected live output: intensity-vs-pixel summary with honesty that wavelength
calibration is separate (`teachspec.calibration`).

## Docs

| Doc | Role |
|-----|------|
| `docs/family/teachspec/SPEC.md` | Locked hardware/software target (USB-cam primary) |
| `docs/family/teachspec/SAFETY.md` | Classroom safety one-pager (live camera still applies) |
| `docs/family/teachspec/BOM_v0.md` | USB-cam path BOM skeleton (TBD prices) |
| `docs/family/teachspec/roadmap.md` / `status.md` | Phase checklist / claim hygiene |
| `teachspec/uvc_ingest.py` | Protocol + stub + optional `UvcOpenCvSource` |
