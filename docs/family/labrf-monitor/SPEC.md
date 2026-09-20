# LabRF Monitor v1 — Locked Spec

**Depends on:** `spectrum_core` Spectrum / peaks / stack; RF backend (pyrtlsdr optional; mock IQ required)  
**Status:** Phase 1 scaffold Implemented (mock); live RTL Planned (hardware-verified)

## Hardware

- RTL-SDR Blog V3/V4 or compatible dongle (receive-only) — **optional**; not required for CI  
- Host: laptop; antenna documented (stock whip OK for v1)

## Software

- Ingest: center frequency, span/sample rate → power spectrum frames → waterfall buffer  
- Mock IQ mode: synthetic / fixture complex IQ → FFT + window → `Spectrum` (x: Hz/MHz, y: dB)  
- UI: spectrum, waterfall heatmap, tunable center/span, educational presets, peak markers  
- Presets (editable JSON): FM broadcast, ISM bands, etc. — **educational presets, not regulatory advice**  
- Optional RTL-SDR adapter behind protocol; clear error if `[labrf]` / `[rtlsdr]` missing  
- Optional threshold → log timestamped events (Planned)

## Non-goals v1

Demodulation beyond power spectrum, multi-dongle correlation, claiming compliance testing,
transmit, chemical identification via RF.

## Deliverables

1. RF ingest adapter + mock IQ fixture mode (tests without dongle) — **Done (Phase 1)**  
2. LabRF UI mode (mock) — **Done (Phase 1)**  
3. Preset pack + disclaimer — **Done (Phase 1)**  
4. Hardware-verified checklist (named dongle + antenna + capture log) — Planned
