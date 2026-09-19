# LabRF Monitor v1 — Locked Spec (Phase 0 design)

**Depends on:** `spectrum-core` waterfall + peak; RF backend (rtl_sdr / Soapy / pyrtlsdr — choose in Phase 1)  
**Status:** Planned — closest hardware cousin to OrcSDR

## Hardware

- RTL-SDR Blog V3/V4 or compatible dongle (receive-only)  
- Host: laptop; antenna documented (stock whip OK for v1)

## Software

- Ingest: center frequency, span/sample rate → power spectrum frames → waterfall buffer  
- UI: live spectrum, waterfall, tunable center/span, peak markers  
- Presets (editable JSON): e.g. FM broadcast, 2.4 GHz ISM, local pager/ISM regions — **label as educational presets, not regulatory advice**  
- Optional threshold → log timestamped events

## Non-goals v1

Demodulation beyond power spectrum, multi-dongle correlation, claiming compliance testing.

## Deliverables

1. RF ingest adapter + mock IQ fixture mode (tests without dongle)  
2. LabRF UI mode  
3. Preset pack + disclaimer  
4. Hardware-verified checklist (named dongle + antenna + capture log)
