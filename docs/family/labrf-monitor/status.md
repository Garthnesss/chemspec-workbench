# Status — LabRF Monitor

**As of:** 2026-09-19 (PT)  
**Phase:** 1 — mock RF path (demo-polish: streaming + threshold + peak-hold/PNG)  
**Blocked on:** named dongle + antenna + capture log for hardware-verified live RTL

## Implemented (Phase 1)

- Package `labrf/` reusing `spectrum_core.Spectrum` / `find_peaks` / `stack`
- `spectrum_core` RF units: `x_unit` `Hz` \| `MHz`, `y_unit` `dB` (plus existing optical units)
- Mock IQ: `generate_synthetic_iq` / `load_iq_fixture` / `fixtures/labrf/mock_iq.npz`
- FFT + window → power spectrum (`iq_to_spectrum`)
- `WaterfallBuffer` (matrix heatmap + `stack` traces)
- Educational presets JSON + disclaimer (“not regulatory advice”)
- Optional RTL-SDR adapter behind protocol; clear ImportError without `[labrf]` / `[rtlsdr]`
- NiceGUI UI: `python -m labrf.ui_app` (port 8081) — mock by default, **no dongle required**
  - **Streaming mock waterfall** — Start/Stop timer pulls successive synthetic IQ frames
  - **Threshold event log** — power threshold (dB); peak / max-bin events; clear; CSV export
  - Quick preset jump buttons, Load mock fixture, provenance strip (source / center / rate / frames)
  - Clearer demo / educational disclaimer (dismissible `ui.card` on NiceGUI 3.x; not `ui.banner`)
- `MockStreamGenerator` + `ThresholdEventLog` / `evaluate_threshold` (pure, unit-tested)
  - Event log **maxlen** (default 500) so long mock streams stay bounded
  - Waterfall **auto-resets** when the frequency axis changes (honest labels after retune)
  - Mock `configure` is a no-op when tune unchanged (no seed thrash every stream tick)
  - Fixture IQ ring-read is vectorized (stream-friendly)
  - Status copy distinguishes mock vs fixture and keeps **receive-only demo** visible
- pytest: mock FFT→spectrum, presets, waterfall, stream frames, threshold logic, no-hardware RTL guard
- **Peak-hold / max-hold** — `PeakHoldTracker` (per-bin max across mock frames; resets on retune/axis change); NiceGUI toggle + overlay
- **PNG export** — `export_spectrum_png` / `export_waterfall_png` (matplotlib Agg; honesty footer; UI download buttons); works without dongle / without claiming hardware-verified

## Next

1. Hardware-verified live RTL-SDR checklist (named Blog V3/V4 + antenna + capture log)
2. Session polish / compare before-after relocating gear (optional)

## Claims

- **Mock / synthetic IQ + streaming demo:** Implemented for CI and UI demos.
- **Live RF / EMI monitoring on real hardware:** *Planned* until hardware-verified STATUS row.
- No demodulation, TX, compliance, or chemical-ID claims.
