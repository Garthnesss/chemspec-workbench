# FID / NMR Playground (Phase 0 software stub)

Educational **FID → FFT → phase → peaks** path for the Spectrum Family.

**Honesty:** Phase-0 is **mock/synthetic only**. No live Bruker/Varian driver,
no magnet required, **no compound ID / structure elucidation**.

## What this package does (now)

- `FID` container: complex time series + `sw_hz`, `obs_mhz`, `ref_ppm`, nucleus
- Exponential apodization (line broadening)
- FFT + zero/first-order phase (`phc0`, `phc1`)
- Carrier-relative **Hz** or teaching **ppm** axis → `spectrum_core.Spectrum`
- Synthetic 1H-like mock FIDs for demos and pytest

## What this package does **not** do yet

- Licensed public FID fixture pack (still Planned)
- UI mode / ChemSpec shell page
- Autophase, 2D NMR, live spectrometer control
- Compound identification or structure elucidation

## Quick try

```bash
fidnmr-demo
# or
python -m fidnmr.demo

pytest -q tests/test_fidnmr.py

# thin examples twin (plot + peaks CSV)
python examples/fidnmr_walkthrough.py --save-dir /tmp/fidnmr_demo
pytest -q tests/test_fidnmr_example.py
```

See `docs/family/fid-nmr-playground/` for Project Truth, SPEC, roadmap, and status.
