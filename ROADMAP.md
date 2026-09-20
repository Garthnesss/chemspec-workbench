# Roadmap — ChemSpec Workbench

| Phase | Name | Status | Outcome |
|-------|------|--------|---------|
| 0 | Scope & docs | Done (docs) | Truth/SPEC/phase0 locked in family |
| 1 | Scaffold + fixtures | Done | `spectrum_core`, tests green, synthetic IR/UV |
| 2 | MVP UI | Done | Open/plot/peaks/baseline/overlay (NiceGUI) |
| 3 | Waterfall + polish | Done | Folder stacks, peak CSV export, A↔%T |
| 3b | Advanced baselines | Done | Optional pybaselines AsLS/MPLS + UI picker |
| 3c | Absorbance + provenance | **Done (this branch)** | UV-Vis y_unit=A mapping; NiceGUI provenance strip |
| 4 | Family handoff | Partial | LabRF mock scaffold in-repo; TeachSpec / FID still design |

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

## Phase 3 checklist

- [x] Peak table export from UI (+ `peaks_to_csv` helper)
- [x] Absorbance ↔ %T helper (core + UI display toggle; limits documented)
- [x] Folder waterfall / stacked view (`ingest_folder` + `stack`)

## Phase 3b checklist

- [x] Optional `[baselines]` extra → `pybaselines` (BSD-3)
- [x] `baseline_correct(method=...)` with polynomial default/fallback
- [x] UI method dropdown (polynomial + asls + mpls when installed)
- [x] Tests: polynomial always; pybaselines in `[dev]` for CI

