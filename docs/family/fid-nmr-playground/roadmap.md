# Roadmap — FID / NMR Playground

| Phase | Name | Status | Outcome |
|-------|------|--------|---------|
| 0 | Design lock + software stub | **Software stub Implemented** | Truth + SPEC + `fidnmr/` mock FID→FFT/phase→Spectrum |
| 1 | Headless polish + fixtures | Planned | Licensed FID fixtures + richer tests |
| 2 | UI mode | **Mock UI Implemented** | Time + spectrum views wired to core (`fidnmr-ui`) |
| 3 | Teaching pack | Planned | Chemistry-reviewed examples |
| 4 | Done | Goal | Truth table satisfied |

## Phase 0 checklist

- [x] Project Truth / SPEC / roadmap  
- [x] Software stub: `FID` + apodize + FFT/phase + Hz/ppm → `Spectrum` + mock source + tests  
- [x] Thin examples walkthrough + pytest smoke (`examples/fidnmr_walkthrough.py`)  
- [x] Gate: ChemSpec core accepts frequency-domain spectra (`Hz`/`ppm` x units)  
- [x] Mock NiceGUI playground (`fidnmr-ui`)  
- [ ] Chemistry: pick first teaching nuclei/examples  
- [ ] Locate 2 licensed FID fixtures  
