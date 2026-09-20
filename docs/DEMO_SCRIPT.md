# Demo script (~30 seconds) — ChemSpec ethanol IR + peaks

**Purpose:** voice-over checklist for a screen recording later (not a live classroom plan).  
**Honesty:** analysis / visualization only — **no compound identification**.

## Setup (before record)

```bash
cd chemspec-workbench
source .venv/bin/activate   # or fresh venv
pip install -e ".[ui,baselines]"
python -m chemspec.ui_app   # http://localhost:8080
```

Alternate headless stills (no UI):

```bash
python - <<'PY'
from pathlib import Path
from spectrum_core import ingest, find_peaks, export_spectrum_png
spec = ingest("fixtures/public/ethanol_ir_pnnl.jdx")
peaks = find_peaks(spec, prominence=0.05)
export_spectrum_png(spec, "docs/screenshots/chemspec-ethanol-ir-peaks.png", peaks=peaks)
print(len(peaks), "peaks")
PY
```

## 30-second beat sheet

| t | Say / do |
|---|----------|
| 0–5 s | “ChemSpec is a software workbench for UV-Vis and IR spectra. It does **not** identify compounds.” |
| 5–12 s | Click **Load public: Ethanol IR**. “Public PNNL/NIST JCAMP — Owner: Public domain. Attribution in SOURCES.md.” |
| 12–20 s | Point at plot + peak table. “Peaks show center, height, prominence, and **prominence-relative FWHM and area** — an explicit measurement contract, not a library match.” |
| 20–26 s | Optional: toggle baseline or open processing history. “Sessions can save raw hash + analysis fingerprint for reproducible teaching.” |
| 26–30 s | “For a DIY optical track, see TeachSpec — USB camera, SAFETY.md first, intensity vs pixel until calibrated.” End on honesty footer / STATUS link. |

## Do not say

- “This proves it’s ethanol” / any compound-ID claim from peaks alone  
- “Hardware-verified wavelength” for TeachSpec webcam frames  
- “Absorbance” for NIST UV-Vis log₁₀(ε) fixtures  

## Assets

- UI capture: `docs/screenshots/chemspec-ethanol-ir.png` (`scripts/capture_chemspec_screenshot.py`)
- Peaks still + short GIF: `docs/screenshots/chemspec-ethanol-ir-peaks.png` / `.gif`
