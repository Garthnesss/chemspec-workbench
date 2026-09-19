# Project Truth — LabRF Monitor

> North star. SPEC, roadmap, and status must agree with this.

## One-sentence goal

Use an **RTL-SDR** to watch the **radio environment around lab instruments**, with ChemSpec-family waterfall/peak UI — so scientists can spot EMI that messes with sensitive measurements.

## Why this exists

OrcSDR-class tools already do spectrum/waterfall. Labs care about *interference near balances, patch clamp, NMR consoles, etc.* This project reuses `spectrum-core` + an RF ingest adapter; it does **not** measure chemical absorbance.

## Feelings we protect

1. **Operational honesty** — This is EMI/situational awareness, not a chemistry assay.  
2. **Familiar viz** — Spectrum + waterfall like teaching SDR tools.  
3. **Actionable** — Markers/presets for common junk (ISM, FM, LTE bands) without fearmongering.  
4. **Safe RF practice** — Receive-only; no transmit.

## What “done” means

| Must | Nice |
|------|------|
| RTL-SDR live spectrum + waterfall | Peak hold / max-hold |
| Frequency presets for lab bands of interest | Simple “event log” when power exceeds threshold |
| Export CSV/PNG of captures | Compare before/after relocating gear |
| Clear disclaimers | Integration notes for OrcSDR-like hardware later |

## Out of scope

Direction finding, decryption, transmitting, claiming FCC certification, chemical identification via RF.
