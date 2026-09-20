# Roadmap — LabRF Monitor

| Phase | Name | Status | Outcome |
|-------|------|--------|---------|
| 0 | Design lock | **Done** | Truth + SPEC |
| 1 | Mock RF path | **Done (demo polish)** | Fixture IQ → spectrum / waterfall + stream + threshold UI |
| 2 | Live RTL-SDR | Planned | Real dongle *hardware-verified* |
| 3 | Presets + logging | **Done** (presets + threshold event log) | Threshold events + session polish |
| 4 | Done | Goal | Truth table met |

## Phase 1 checklist

- [x] Choose Python RF stack: **pyrtlsdr** optional extra; mock default
- [x] Mock IQ fixture format (`.npz` complex + meta)
- [x] FFT → `Spectrum` (Hz/MHz, dB) via `spectrum_core`
- [x] Waterfall buffer
- [x] Educational presets JSON + disclaimer
- [x] NiceGUI mock UI (streaming waterfall + threshold log)
- [x] pytest without hardware
- [ ] Gate: hardware-verified live path (Phase 2)
