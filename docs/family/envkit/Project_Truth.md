# Project Truth — EnvKit

> North star. SPEC, roadmap, and status must agree with this.

## One-sentence goal

A **later-phase environmental sensing kit** that logs time-series / spectral-ish sensor data into the same workbench family — for education and open science, not certified monitoring.

## Why this exists

Once ChemSpec (and optionally TeachSpec/LabRF) exist, EnvKit answers “what about air/water/field sensors?” Same truth labels and UI patterns; different transducers.

## Feelings we protect

1. **Provisional** — Ships after the core family proves itself.  
2. **Cited methods** — Sensor choice and limitations documented; no “detects all pollutants.”  
3. **Provenance** — Every run stores sensor ID, calibration date, location note.  
4. **Family fit** — Uses `spectrum-core` *or* a sibling `timeseries-core` if data aren’t truly spectral.

## What “done” means (future)

| Must | Nice |
|------|------|
| ≥1 vetted sensor path with calibration story | Multi-sensor backpack kit |
| Logging + plot in family UI | Field checklist PDF |
| Explicit non-claims list | Community recipe book |

## Out of scope (always)

Regulatory compliance monitoring, medical claims, “AI identifies contamination” without validated models.
