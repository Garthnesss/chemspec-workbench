# Project Truth — TeachSpec

> North star. SPEC, roadmap, and status must agree with this.

## One-sentence goal

Build a **low-cost optical teaching spectrometer** whose live spectrum UI speaks the same language as ChemSpec / SDR tools — so students *see* absorbance/emission without a $5k instrument.

## Why this exists

ChemSpec Workbench teaches spectrum *literacy* from files. TeachSpec teaches spectrum *acquisition*: light → grating → sensor → peaks. Same `spectrum-core` plot/peak/baseline; different ingest (**v1 primary: USB camera / UVC**; linear CCD/CMOS Planned alternate).

## Feelings we protect

1. **Immediate** — Hold a sample / lamp, see a spectrum update live.
2. **Honest** — Wavelength axis is calibrated and labeled with uncertainty; no fake “lab grade.”
3. **Same UI language** — Peaks, baseline, waterfall feel like ChemSpec.
4. **Buildable** — BOM under a clear budget; reproducible enclosure + calibration lamp path.
5. **Classroom-safe** — No clinical claims; visible-light default; see SAFETY.md (no UV-C in v1 kits).

## What “done” means (finished product)

| Must | Nice |
|------|------|
| Calibrated wavelength axis (Hg/CFL or known lines) | Auto peak labels for teaching lines |
| Live spectrum into ChemSpec-compatible UI | 3D-printed enclosure plans |
| Documented BOM + build guide | Phone-camera fallback mode |
| Safety one-pager | Multi-unit classroom kit list |

## Out of scope (product)

Research-grade accuracy, regulated diagnostics, replacing ChemSpec file workflows.
