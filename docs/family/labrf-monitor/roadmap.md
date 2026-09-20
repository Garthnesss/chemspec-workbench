# Roadmap — LabRF Monitor

| Phase | Name | Status | Outcome |
|-------|------|--------|---------|
| 0 | Design lock | **Done** | Truth + SPEC |
| 1 | Mock RF path | **Now (scaffold)** | Fixture IQ → spectrum / waterfall tests + UI |
| 2 | Live RTL-SDR | Planned | Real dongle *hardware-verified* |
| 3 | Presets + logging | Partial (presets done) | Threshold event log + session polish |
| 4 | Done | Goal | Truth table met |

## Phase 1 checklist

- [x] Choose Python RF stack: **pyrtlsdr** optional extra; mock default
- [x] Mock IQ fixture format (`.npz` complex + meta)
- [x] FFT → `Spectrum` (Hz/MHz, dB) via `spectrum_core`
- [x] Waterfall buffer
- [x] Educational presets JSON + disclaimer
- [x] Minimal NiceGUI mock UI
- [x] pytest without hardware
- [ ] Gate: hardware-verified live path (Phase 2)
