# Roadmap — LabRF Monitor

| Phase | Name | Status | Outcome |
|-------|------|--------|---------|
| 0 | Design lock | **Now** | Truth + SPEC |
| 1 | Mock RF path | Planned | Fixture IQ → waterfall tests |
| 2 | Live RTL-SDR | Planned | Real dongle *hardware-verified* |
| 3 | Presets + logging | Planned | Lab-usable session tool |
| 4 | Done | Goal | Truth table met |

## Phase 0 checklist

- [x] Docs drafted  
- [ ] Choose Python RF stack (pyrtlsdr vs Soapy)  
- [ ] Mock IQ fixture format defined  
- [ ] Gate: waterfall API stable in `spectrum-core`
