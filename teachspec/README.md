# TeachSpec (Phase 0 software stub)

Educational optical teaching spectrometer **software** path for the Spectrum Family.

## What this package does (now)

- Pixel → nm **linear** (and optional **quadratic**) calibration from ≥2 known lines
- Save / load calibration JSON
- `OpticalLiveFrame` (1-D intensity + meta) → `spectrum_core.Spectrum` after calibration
- Synthetic CFL-like mock frames for demos and pytest (**no camera libraries**)

## What this package does **not** do yet

- Choose USB-cam vs linear CCD (human gate — not locked in code)
- BOM / enclosure / live camera drivers
- Compound identification
- Hardware-verified wavelength claims

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

See `docs/family/teachspec/` for Project Truth, SPEC, roadmap, and status.
