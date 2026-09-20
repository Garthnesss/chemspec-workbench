# Classroom pilot one-pager — ChemSpec + TeachSpec (ask)

**To:** chemistry / physical-science instructor considering a short software or DIY-optics pilot  
**From:** ChemSpec Workbench / Spectrum Family (open source, MIT)  
**Ask:** 1–2 lab periods of honest spectrum literacy — **not** compound identification

---

## Learning outcomes (what students practice)

1. **Spectrum literacy** — read wavelength / wavenumber axes; distinguish intensity vs absorbance vs %T; notice when public UV-Vis data is log₁₀(ε) (intensity), not absorbance.
2. **Reproducible sessions** — load a fixture or file, apply a short processing pipeline (baseline / smooth), save a `.csw.json` analysis session with hashes — redo the same steps later.
3. **FWHM honesty** — report peak center / height / **prominence-relative FWHM and area** using the stated measurement contract (not “magic ID numbers”).

ChemSpec does **not** identify compounds, match libraries as proof of structure, or drive spectrometers. TeachSpec does **not** claim metrology-grade wavelength from a webcam alone.

## Time box

| Track | Contact time | Prep |
|-------|--------------|------|
| **A — Software-only** | 1 lab period (~50–90 min) | Laptop + `pip install`; public ethanol IR + one UV-Vis fixture |
| **B — TeachSpec USB kit** | 1–2 lab periods | Track A software **plus** DIY UVC kit (see BOM); SAFETY review first |

## Two tracks

### Track A — Software-only (recommended first)

- Install: `pip install "chemspec-workbench[ui,baselines]"` (or editable checkout — see README).
- Run: `chemspec-ui` → load **public Ethanol IR** → peaks table (FWHM/area) → optional session save.
- Optional: one NIST UV-Vis public fixture (benzene / acetone / naphthalene) with log₁₀(ε) honesty call-out.
- No chemicals required beyond what your curriculum already allows for discussion; fixtures are public-domain / attributed files in-repo.

### Track B — TeachSpec USB-camera kit (optional hardware)

- Same ChemSpec literacy goals, plus a **visible-light teaching spectrometer** path: USB webcam (UVC) + transmission grating or DVD method + slit + dark enclosure + CFL calibrator.
- Software: `teachspec-ui` (Mock default) or optional live UVC (`pip install "chemspec-workbench[ui,teachspec]"`). Live frames are **intensity vs pixel** until students apply a known-line calibration — say that out loud.
- Kit budget target: **under ~$75** for software + optics DIY (laptop assumed on hand). Parts classes and search keywords: [`docs/family/teachspec/BOM_v0.md`](family/teachspec/BOM_v0.md). Prices are approximate and change.
- **Read first:** [`docs/family/teachspec/SAFETY.md`](family/teachspec/SAFETY.md) — visible light only; no UV-C / germicidal lamps; no staring into lamps; USB 5V camera only; teacher supervision.

## What we need from you

1. **Safety / lab-policy OK** for Track B (if used) — your institution’s rules win.
2. **1–2 class periods** and a short note afterward: what clicked, what confused, what you would cut.
3. **No compound-ID expectations** in grading rubrics — spectrum literacy and reproducibility only.
4. Optional: anonymized screenshots or session files (no student PII) for docs improvement.

## What you get

- Open-source MIT software + public fixtures with attribution (`fixtures/public/SOURCES.md`).
- Explicit measurement contract and session hashes for “show your work.”
- Honest labels: Experimental siblings (TeachSpec / LabRF / FID-NMR) stay labeled Experimental.

## Explicit non-claims

- No clinical / forensic / regulatory use.
- No “this peak proves this molecule.”
- No hardware-verified wavelength from camera alone without calibration + residuals discussion.
- No PyPI “official curriculum endorsement” — this is a pilot ask, not a product certification.

## Links

| Doc | Path |
|-----|------|
| Safety (TeachSpec) | [`docs/family/teachspec/SAFETY.md`](family/teachspec/SAFETY.md) |
| Kit BOM (approx.) | [`docs/family/teachspec/BOM_v0.md`](family/teachspec/BOM_v0.md) |
| Release 0.2 checklist | [`docs/RELEASE_0.2.md`](RELEASE_0.2.md) |
| Repo | https://github.com/Garthnesss/chemspec-workbench |

---

*One page by design. Questions → open a GitHub issue on the repo. Thank you for teaching carefully.*
