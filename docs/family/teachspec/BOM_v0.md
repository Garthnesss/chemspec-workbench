# TeachSpec BOM v0 — USB-camera (UVC) path

**Status:** skeleton / drafting — placeholder line items and **rough TBD** cost ranges.  
**Not** a vendor commitment, quote, or purchasing approval.  
**Sensor lock:** USB camera (UVC) is v1 primary; linear CCD/CMOS is Phase 2+ alternate (not on this BOM).  
**Safety:** read [`SAFETY.md`](SAFETY.md) before sourcing lamps or running classroom demos.

## Line items

| Item | Example part class | Qty | Est. unit $ (rough TBD) | Notes | License / sourcing |
|------|--------------------|-----|-------------------------|-------|--------------------|
| UVC webcam | Generic UVC USB camera (720p–1080p class; fixed or manual focus preferred) | 1 | TBD ~$15–60 | Primary v1 sensor. Prefer well-supported UVC; no proprietary-only drivers required for Phase-1 goal. | Commodity USB; check local education procurement |
| Transmission grating | ~1000 ln/mm transmission grating **or** DVD teaching variant | 1 | TBD ~$5–40 (film) / ~$0–5 (DVD) | Mark **TBD** which variant the kit documents. DVD path is teaching-only; note dispersion / blaze differences. | Education / surplus optics; DVD is consumer media — document teaching fair-use intent |
| Slit | Fixed mechanical slit (razor + spacer, 3D-printed slit card, or purchased slit) | 1 | TBD ~$0–15 | Width affects resolution vs throughput; document nominal gap in build guide. | DIY or lab-supply |
| Housing / enclosure | Cardboard / foamcore / 3D-printed light baffle + camera mount | 1 | TBD ~$0–25 | Prefer enclosure so students watch the screen, not the lamp (see SAFETY.md). | DIY; publish printable files later if any |
| CFL / neon calibrator | Compact fluorescent or neon teaching lamp (visible lines) | 1 | TBD ~$5–25 | Prefer CFL/neon. Hg discharge only with teacher control + eye notes — see SAFETY.md. **No UV-C / germicidal.** | Consumer / teaching-lab supply |
| Host laptop USB | Existing classroom laptop with free USB-A/C port (+ hub if needed) | 1 | $0 (assumed on hand) | USB 5V camera only; no mains mods. | Institution-owned host |
| Optional: USB extension / powered hub | Short USB 2.0/3.x extension or hub | 0–1 | TBD ~$5–20 | Only if cable length / port power needs it. Stay within camera power budget. | Commodity USB |
| Optional: diffuse visible desk lamp | Low-power visible lamp for rough demos | 0–1 | TBD ~$5–20 | Not a line calibrator; optional fill. | Consumer |

## Cost posture

- Rough kit hardware (excluding laptop): **TBD ~$30–150** depending on grating choice and enclosure ambition.
- Ranges above are **order-of-magnitude placeholders** for planning — replace with dated quotes before any “kit price” claim in README/STATUS.
- Do **not** treat this table as Implemented purchasing guidance.

## Out of this BOM (v1)

- Linear CCD/CMOS modules (Phase 2+ alternate)
- UV-C / germicidal lamps
- Mains-powered custom electronics / ESP32 tethered mode (optional later; not required for USB-cam path)
- Phone-camera fallback as primary (Nice-to-have in Project Truth; not v1 kit SKU)

## Next

1. Teacher safety review of SAFETY.md  
2. Pick grating variant (1000 ln/mm vs DVD) and freeze one kit SKU  
3. Replace TBD ranges with dated example SKUs / quotes  
4. Live UVC OpenCV ingest (software) — optional `[teachspec]` extra Implemented in-repo; hardware bench spike still separate from this BOM doc
