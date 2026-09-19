# EnvKit v1 — Locked Spec (Phase 0 design / parked)

**Depends on:** ChemSpec family maturity; Chemistry + local use-case pick  
**Status:** Deferred design — document now, build later

## Decision gate (must pass before Phase 1)

Pick **one** first modality:

A. Optical colorimetry (LED + photodiode / TeachSpec cousin)  
B. Electrochem / pH / conductivity time-series  
C. Particulate (PM) + metadata (not a spectrum — may need timeseries adapter)

## Software shape

- Ingest → family UI (live plot, log, export)  
- Calibration record required before *hardware-verified*  
- Heavy reuse of ChemSpec session/export patterns

## Non-goals v1

Multi-hazard fusion AI, drone platforms, certified EPA/EU methods.

## Deliverables (when un-parked)

1. Modality decision record  
2. BOM + calibration SOP  
3. Ingest adapter + fixture tests  
4. Field disclaimer + Chemistry review
