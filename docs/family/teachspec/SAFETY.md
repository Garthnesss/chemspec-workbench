# TeachSpec — Classroom Safety One-Pager (v1)

**Audience:** teachers / lab supervisors building or running a TeachSpec USB-camera kit.  
**Scope:** visible-light teaching spectrometer. Not a product safety certification.

## Default operating envelope

- **Visible light only** for v1 classroom kits.
- TeachSpec shows teaching spectra (peaks, calibration literacy). It does **not** make clinical, diagnostic, forensic, or compound-identification claims.
- Wavelength axes are **teaching-calibrated** (known-line fit + residuals), **not** metrology-grade.

## Light sources

| Prefer | Conditional | Do not use in v1 kits |
|--------|-------------|------------------------|
| CFL / compact fluorescent teaching lamps | Hg discharge **only** with teacher control + eye-protection notes | UV-C / germicidal lamps |
| Neon or other low-power visible teaching discharge tubes (teacher-supervised) | Direct sun / bright outdoor sky only with enclosure + no staring | High-power lasers as calibration sources |
| Diffuse desk / room lamps for rough demos | — | Any intentional deep-UV or actinic source |

**Hg discharge:** teacher operates the lamp; students observe the spectrum via the camera path, not by staring into the tube. Provide eye-protection guidance consistent with your institution’s lab policy when a discharge tube is used.

## Eye safety

- Do **not** stare into lamps, discharge tubes, or concentrated beams.
- Prefer an enclosure or baffle so the camera sees the source and students see the screen.
- Never point a laser into the slit or at eyes. Lasers are out of scope for v1 kits.

## Electrical

- **USB 5V camera only** (UVC webcam class). No mains wiring mods, no custom high-voltage supplies, no “hack the wall wart” paths in v1.
- Use a normal laptop USB port / powered hub rated for the camera. Follow the camera vendor’s ratings.
- Keep liquids away from the laptop and USB connectors.

## Supervision & age-appropriate use

- Run builds and live demos under **teacher / adult lab supervision**.
- Follow your school or maker-space age and lab-safety rules (PPE, no unsupervised discharge lamps, no tasting/handling unknown chemicals as “samples” without a curriculum plan).
- Chemical samples (if any) must come from an approved teaching list for your institution — TeachSpec does not authorize hazardous reagents.

## Explicit non-goals (safety-relevant)

- No clinical / medical / diagnostic use.
- No compound identification or “what is this substance?” claims from peaks alone.
- No UV-C / germicidal lamp kits in v1.
- No mains electrical modifications.
- No metrology or regulatory certification claims from classroom calibration.

## Related docs

- Hardware target + sensor lock: `SPEC.md`
- Rough parts list: `BOM_v0.md`
- Software honesty (mock-only Phase 0): `../../../../teachspec/README.md` and family `status.md`
