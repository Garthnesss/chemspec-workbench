# Roadmap — ChemSpec Workbench

| Phase | Name | Status | Outcome |
|-------|------|--------|---------|
| 0 | Scope & docs | Done (docs) | Truth/SPEC/phase0 locked in family |
| 1 | Scaffold + fixtures | Done | `spectrum_core`, tests green, synthetic IR/UV |
| 2 | MVP UI | Done | Open/plot/peaks/baseline/overlay (NiceGUI) |
| 3 | Waterfall + polish | Done | Folder stacks, peak CSV export, A↔%T |
| 3b | Advanced baselines | Done | Optional pybaselines AsLS/MPLS + UI picker |
| 3c | Absorbance + provenance | Done | UV-Vis y_unit=A mapping; NiceGUI provenance strip |
| 4 | Family handoff | Partial | Public NIST UV-Vis fixtures + benzene/acetone/naphthalene tutorial trio Done; LabRF mock polish; TeachSpec Phase-0 + USB-cam lock; FID/NMR Phase-0 software stub |

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
- [x] Peak FWHM + half-max area on `Peak` / CSV / UI table
- [x] Absorbance ↔ %T helper (core + UI display toggle; limits documented)
- [x] Folder waterfall / stacked view (`ingest_folder` + `stack`)
- [x] Optional 3-D surface for folder traces (`spectra_to_surface`; series index ≠ time)
- [x] NiceGUI folder-waterfall **3-D surface** checkbox (`state.view_3d` → `plot3d.build_surface_figure`)
- [x] Analysis session save/load (`.csw.json` / `spectrum_core.session`)
- [x] Processing pipeline + history (`spectrum_core.processing`; UI 2a)

## Phase 3b checklist

- [x] Optional `[baselines]` extra → `pybaselines` (BSD-3)
- [x] `baseline_correct(method=...)` with polynomial default/fallback
- [x] UI method dropdown (polynomial + asls + mpls when installed)
- [x] Tests: polynomial always; pybaselines in `[dev]` for CI

## Phase 4 checklist

- [x] Public NIST UV-Vis fixtures (benzene / acetone / naphthalene) + SOURCES honesty (log₁₀(ε) ≠ absorbance)
- [x] UV-Vis tutorial trio (walkthrough notebook + `.py` twins; pytest smoke, no nbconvert CI)
- [x] LabRF mock demo polish in-repo (stream / threshold / peak-hold / PNG)
- [x] TeachSpec Phase-0 software stub (cal + mock frames; no live camera)
- [x] TeachSpec v1 sensor lock: USB camera (UVC) primary; SAFETY.md + BOM_v0 skeleton (docs)
- [x] TeachSpec UVC ingest interface stub (`UvcIngestStub` → NotImplementedError; no OpenCV)
- [x] FID-NMR Phase-0 software stub (mock FID→FFT/phase; no magnet)
- [x] FID-NMR thin examples walkthrough + pytest smoke (`examples/fidnmr_walkthrough.py`; no notebook yet)
- [ ] Broader chemistry sign-off / more public real examples beyond the three NIST UV-Vis fixtures

## ChemSpec 0.2 — Measurement Integrity + TeachSpec UVC (release-prep Done)

- [x] Peak measurement contract (prominence-relative FWHM/area + explicit Peak fields / CSV / UI)
- [x] Session hashes + computational identity (`raw_data_hash`, fingerprint, format_version 2 + v1 migrate)
- [x] Operation preconditions (smooth/baseline/normalize/despike → ProcessingError)
- [x] Schema migration fixtures (`tests/fixtures/sessions/session_v1.json` + current)
- [x] README Experimental framing for LabRF/TeachSpec + STATUS/ROADMAP + AUDIT doc
- [x] TeachSpec UVC ingest stub → optional OpenCV live → NiceGUI `teachspec-ui` (Mock default)
- [x] Version bump to **0.2.0** + Keep-a-Changelog `CHANGELOG.md` + `docs/RELEASE_0.2.md` checklist
- [x] Classroom pilot one-pager (`docs/classroom_pilot_one_pager.md`)
- [ ] **PyPI / TestPyPI publish** — waiting on maintainer credentials (user runs `twine`; see `docs/RELEASE_0.2.md`)
