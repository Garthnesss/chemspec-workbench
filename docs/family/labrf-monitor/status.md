# Status — LabRF Monitor

**As of:** 2026-09-19 (PT)  
**Phase:** 1 — mock RF path (software-first scaffold)  
**Blocked on:** named dongle + antenna + capture log for hardware-verified live RTL

## Implemented (Phase 1 scaffold)

- Package `labrf/` reusing `spectrum_core.Spectrum` / `find_peaks` / `stack`
- `spectrum_core` RF units: `x_unit` `Hz` \| `MHz`, `y_unit` `dB` (plus existing optical units)
- Mock IQ: `generate_synthetic_iq` / `load_iq_fixture` / `fixtures/labrf/mock_iq.npz`
- FFT + window → power spectrum (`iq_to_spectrum`)
- `WaterfallBuffer` (matrix heatmap + `stack` traces)
- Educational presets JSON + disclaimer (“not regulatory advice”)
- Optional RTL-SDR adapter behind protocol; clear ImportError without `[labrf]` / `[rtlsdr]`
- Minimal NiceGUI UI: `python -m labrf.ui_app` (port 8081) — mock only by default
- pytest: mock FFT→spectrum, presets, waterfall, no-hardware RTL guard

## Next

1. Hardware-verified live RTL-SDR checklist (named Blog V3/V4 + antenna + capture log)
2. Threshold event log (optional)
3. Export CSV/PNG of captures
4. Peak-hold / max-hold

## Claims

- **Mock / synthetic IQ:** Implemented for CI and UI demos.
- **Live RF / EMI monitoring on real hardware:** *Planned* until hardware-verified STATUS row.
- No demodulation, TX, compliance, or chemical-ID claims.
