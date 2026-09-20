# TeachSpec BOM v0 — USB-camera (UVC) path (teacher-orderable)

**Status:** purchasable-class draft — **example product types**, search keywords, and
**approximate USD ranges** for classroom planning.  
**Not** a vendor quote, purchasing approval, or affiliate catalog.  
**No fake SKUs** — prices change; treat every `$` band as an estimate as of drafting
(2026-09). Re-check Amazon / Adafruit / Thorlabs / education suppliers before ordering.

**Sensor lock:** USB camera (UVC) is v1 primary; linear CCD/CMOS is Phase 2+ alternate
(not on this BOM).  
**Safety:** read [`SAFETY.md`](SAFETY.md) before sourcing lamps or running classroom demos.  
**Budget target:** **under ~$75** for software + optics DIY kit hardware (**laptop assumed
on hand**, not counted in the band).

## How to use this table

1. Prefer **search keywords** over any remembered brand name.
2. Pick one grating path (sheet **or** DVD teaching method) — do not buy both for v1.
3. Keep the enclosure dark enough that students watch the **screen**, not the lamp.
4. Log your actual receipts dated; replace ranges here when you have quotes.

## Line items (purchasable classes)

| Item | Purchasable class / example product type | Qty | Approx. USD (rough) | Search keywords (Amazon / Adafruit / Thorlabs-class) | Notes |
|------|------------------------------------------|-----|---------------------|------------------------------------------------------|-------|
| **UVC webcam** | Generic UVC USB webcam, 720p–1080p class; fixed or manual focus preferred; avoid proprietary-only driver sticks | 1 | **~$15–45** | `UVC webcam USB`, `USB camera module UVC`, `ELP USB camera` (class only — verify UVC), `webcam manual focus` | Primary v1 sensor. Must enumerate as standard UVC on the classroom OS. No custom mains power. |
| **Transmission grating sheet** *or* **DVD method** | (A) ~1000 lines/mm transmission grating film/sheet slide-size; **or** (B) sacrificial DVD/CD teaching diffraction (document fair-use / teaching intent) | 1 | **(A) ~$8–35** / **(B) ~$0–5** | (A) `1000 lines/mm transmission grating`, `diffraction grating sheet education`, Thorlabs-class `transmission grating`; (B) `DVD-R` (teaching dispersion only) | Mark which variant your kit docs freeze. DVD path is teaching-only; blaze/dispersion differ from lab gratings. |
| **Slit materials** | Razor-blade + shim/spacer card, 3D-printed slit card, black poster-board knife-edge pair, or purchased adjustable slit (optional upgrade) | 1 | **~$0–15** (DIY) / **~$20–60** (purchased slit — optional, can blow <$75 band) | `razor blades single edge`, `feeler gauge shim`, `3D print spectrometer slit`, `optical slit adjustable` | Narrower slit → better resolution, less light. Document nominal gap in the build guide. Prefer DIY for budget band. |
| **Black enclosure** | Foamcore / cardboard light baffle + camera mount; optional later 3D-printed housing (**TBD** printable files) | 1 | **~$5–20** foamcore DIY; 3D-print filament **TBD ~$5–15** if printing | `black foam core board`, `cardboard project box`, `light baffle`, `matte black spray paint` (ventilate) | Enclosure so camera sees source and students see laptop screen (see SAFETY.md). No need for CNC. |
| **CFL calibrator bulb** | Compact fluorescent teaching lamp (visible Hg/phosphor lines) or neon teaching tube (teacher-supervised) | 1 | **~$5–20** | `CFL bulb`, `compact fluorescent lamp`, `neon indicator lamp education` | Prefer CFL/neon. **No UV-C / germicidal.** Hg discharge only with teacher control + eye notes — SAFETY.md. |
| **USB cable / hub** | Short USB-A/C cable matching the webcam; optional powered USB 2.0/3.x hub if port power is weak | 1 | **~$0–15** (often included with cam) / hub **~$8–20** optional | `USB extension 2.0`, `powered USB hub`, `USB-C to USB-A adapter` | Stay within camera 5V budget. No cable mods. |
| **Host laptop** | Existing classroom / student laptop with free USB port | 1 | **$0 (assumed)** | — | Not in the <$75 kit band. Linux / Windows / macOS with Python 3.10+. |
| **Optional: diffuse visible desk lamp** | Low-power LED/desk lamp for rough continuum demos (not a line calibrator) | 0–1 | **~$5–20** | `LED desk lamp`, `clip lamp LED` | Optional fill only. |

### Budget roll-up (approximate)

| Kit flavor | Typical sum (excl. laptop) | Fits <$75 DIY band? |
|------------|----------------------------|---------------------|
| **DVD + foamcore DIY** | webcam $25 + DVD $2 + slit DIY $3 + foamcore $10 + CFL $10 + cable $0 ≈ **~$50** | **Yes** (headroom) |
| **Grating sheet + foamcore** | webcam $25 + grating $20 + slit $5 + foamcore $10 + CFL $10 ≈ **~$70** | **Usually yes** |
| **Grating + purchased slit + hub** | can reach **~$90–120** | **No** — drop purchased slit / hub to stay in band |

Ranges are **order-of-magnitude planning estimates**. They are **not** Implemented purchasing guidance and **not** a kit SKU price claim for README marketing.

## Software (not hardware BOM, but required)

| Piece | How | Approx. cost |
|-------|-----|--------------|
| ChemSpec / TeachSpec software | `pip install "chemspec-workbench[ui,teachspec]"` when 0.2 is on PyPI, or editable git checkout today | **$0** (MIT) |
| Python 3.10+ | System / python.org / class image | $0–institution |

Live UVC needs the `[teachspec]` extra (OpenCV). Mock preview works with `[ui]` alone (`teachspec-ui` defaults to Mock).

## Out of this BOM (v1)

- Linear CCD/CMOS modules (Phase 2+ alternate)
- UV-C / germicidal lamps
- Mains-powered custom electronics / ESP32 tethered mode (optional later; not required for USB-cam path)
- Phone-camera fallback as primary (Nice-to-have in Project Truth; not v1 kit SKU)
- Affiliate links / guaranteed-in-stock SKUs

## Next

1. Teacher safety review of SAFETY.md  
2. Freeze one grating variant (1000 ln/mm sheet vs DVD) in a build guide  
3. Replace approximate ranges with **dated** local quotes when a pilot school orders  
4. Publish foamcore cut list / optional 3D-print files when stable (**TBD**)  
5. Hardware bench spike remains separate from this BOM doc (optional OpenCV live + NiceGUI preview already Implemented in software)

## Related

- Safety: [`SAFETY.md`](SAFETY.md)
- Classroom pilot ask: [`../../classroom_pilot_one_pager.md`](../../classroom_pilot_one_pager.md)
- Release prep: [`../../RELEASE_0.2.md`](../../RELEASE_0.2.md)
