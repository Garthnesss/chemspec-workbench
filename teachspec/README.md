# TeachSpec (Phase 0 software stub)

Educational optical teaching spectrometer **software** path for the Spectrum Family.

## What this package does (now)

- Pixel → nm **linear** (and optional **quadratic**) calibration from ≥2 known lines
- Save / load calibration JSON
- `OpticalLiveFrame` (1-D intensity + meta) → `spectrum_core.Spectrum` after calibration
- Synthetic CFL-like mock frames for demos and pytest (**no camera libraries**)

## What this package does **not** do yet

- Choose USB-cam vs linear CCD (human gate)
- BOM / enclosure / live camera drivers
- Compound identification
- Hardware-verified wavelength claims

## Quick try

```bash
pip install -e ".[dev]"
python -m teachspec.demo
pytest -q tests/test_teachspec.py
```

See `docs/family/teachspec/` for Project Truth, SPEC, roadmap, and status.
