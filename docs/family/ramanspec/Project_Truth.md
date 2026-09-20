# Project Truth — RamanSpec (pivot sketch)

> Draft / not Implemented. North star for a possible sharp turn. Must not dilute ChemSpec’s teaching honesty.

## One-sentence goal

Build an **open Raman (and probe) assist workbench** that reuses `spectrum_core` to ingest Raman-shift spectra, process them reproducibly, and return **ranked library candidates with scores — never silent compound identity**.

## Why this exists

ChemSpec already teaches UV-Vis/IR literacy and measurement integrity. Raman probes are commercially hot (materials, plastics, teaching forensics) and map cleanly onto the same Spectrum model (`x` in cm⁻¹ Raman shift). The market temptation is “point and ID.” Our wedge is the opposite: **assist + audit trail**, so students and techs learn *why* a hit looks good — and when it doesn’t.

## Feelings we protect

1. **Immediate** — Load a Raman trace (file or future USB spectrometer), see peaks in seconds.
2. **Honest** — UI always says *candidates / similarity*, never *identified as*.
3. **Same language as ChemSpec** — baseline, peaks, FWHM/area contract, session hash/fingerprint.
4. **Buildable** — Start software-only (JCAMP/CSV + open libraries); hardware adapters later.
5. **Classroom- and field-safe** — Laser class documentation required before any live laser path.

## What “done” means (v1 software)

| Must | Nice |
|------|------|
| Ingest Raman JCAMP/CSV → `Spectrum` (cm⁻¹) | USB spectrometer vendor adapter |
| Baseline suited to fluorescence backgrounds | Hit-quality explanations (which peaks drove score) |
| Peak pick with existing measurement contract | Mixture “flag as likely mixed” heuristic |
| Library *search*: top-k cosine / correlation scores | Narrow vertical library (e.g. polymers teaching set) |
| Session save with raw hash + search parameters | Offline library pack with licenses documented |
| Explicit non-ID disclaimers in UI + export | |

## Out of scope (product)

Clinical/diagnostic ID, controlled-substance determination, courtroom expert systems, “AI identifies any chemical,” silent auto-labeling of unknowns.
