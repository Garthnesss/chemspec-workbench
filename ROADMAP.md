# Roadmap — ChemSpec Workbench

| Phase | Name | Status | Outcome |
|-------|------|--------|---------|
| 0 | Scope & docs | Done (docs) | Truth/SPEC/phase0 locked in family |
| 1 | Scaffold + fixtures | Done | `spectrum_core`, tests green, synthetic IR/UV |
| 2 | MVP UI | **In progress / this branch** | Open/plot/peaks/baseline/overlay (NiceGUI) |
| 3 | Waterfall + polish | Planned | Folder time stacks, export peak table UI |
| 4 | Family handoff | Planned | Core stable for TeachSpec / FID / LabRF |

## Phase 1 checklist

- [x] Scaffold `spectrum_core` + app demos
- [x] `AGENTS.md` + `PROJECT_TRUTH.md` + STATUS
- [x] Tests: CSV ingest + peak pick + baseline
- [x] JCAMP-DX basic ingest (MIT `jcamp`) + offline fixtures
- [ ] Chemistry: confirm formats / real public fixtures (human gate)

## Phase 2 checklist

- [x] NiceGUI app with Plotly zoom/pan
- [x] Fixture shortcuts + column sniff/mapping
- [x] JCAMP `.jdx`/`.dx` load in UI (clear parse errors)
- [x] Peak table + prominence + baseline toggle + overlay
- [ ] Peak table export from UI
- [ ] Absorbance ↔ %T helper
