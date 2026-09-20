# Project Truth — FID / NMR Playground

> North star. SPEC, roadmap, and status must agree with this.

## One-sentence goal

Turn **public NMR FID datasets** into an interactive spectrum playground that reuses `spectrum-core` — so learners see FID → FFT → phase → peaks without access to a magnet.

## Why this exists

NMR is the chemistry spectrum students hear about but rarely *touch*. FIDs are IQ-like time series; the math kinship with SDR is real. This project teaches that pipeline honestly, on open data.

## Feelings we protect

1. **Pipeline clarity** — FID, window, FFT, phase, ppm axis are visible steps—not a black box.  
2. **Honest scope** — Educational / open-data only; not a clinical spectrometer.  
3. **Same core** — Peak/baseline/waterfall share ChemSpec DNA.  
4. **No magnet required** — Works fully offline from fixtures.

## What “done” means

| Must | Nice |
|------|------|
| Load FID fixture → show time + frequency views | Simple autophase |
| Manual phase (0/1st order) | Overlay multiple 1H examples |
| ppm axis with referenced solvent/TMS meta | J-coupling cursor helpers |
| Peak pick + export | Minimal 13C example set |

## Phase 0 note

A **mock/synthetic** FID→FFT→phase path (`fidnmr/`) is Implemented for demos and tests. Public licensed FID fixtures and UI remain Planned. Educational only — no compound ID.

## Out of scope

Pulse-sequence design, real spectrometer control, structure elucidation AI that overclaims, 2D NMR (later phase).
