# Changelog

All notable changes to **chemspec-workbench** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **FID/NMR NiceGUI playground** — `fidnmr-ui` / `python -m fidnmr.ui_app` (port 8083);
  mock FID time + real-FFT spectrum, lb/phc0/phc1, ppm/Hz toggle; synthetic only
- **TeachSpec preview nm axis** — optional load of `teachspec.calibration` JSON in
  `teachspec-ui` (educational fit residuals only; **not** CFL auto-cal / **not**
  hardware-verified wavelength)

### Planned

- PyPI publish of `0.2.0` (waiting on maintainer credentials — see `docs/RELEASE_0.2.md`)
- TeachSpec priced/vendor-locked BOM + hardware-verified calibration path + CFL auto-cal
- Classroom pilot feedback incorporation
- FID/NMR licensed public fixtures

## [0.2.0] — 2026-09-20

**Theme:** Measurement Integrity + TeachSpec UVC story.

Honesty reminder: ChemSpec / TeachSpec / LabRF / FID-NMR do **not** identify compounds.
TeachSpec live UVC frames are intensity vs pixel until calibrated; not hardware-verified
wavelength by camera alone. Public UV-Vis fixtures use log₁₀(ε) → intensity, **not** absorbance.

### Added

- **Peak measurement contract** — prominence-relative FWHM/area with explicit Peak fields
  (`width_definition`, `half_max_level`, boundaries, `area_definition`, `baseline_reference_note`);
  CSV + NiceGUI table + session JSON export the contract
- **Session computational identity** — `raw_data_hash`, `analysis_fingerprint`,
  `format_version` 2 with v1 migrate on load; schema fixtures + round-trip tests
- **Processing op preconditions** — smooth / baseline / normalize / despike raise
  `ProcessingError` with clear scientific messages on invalid params
- **Measurement diagnostics** — SNR (MAD-Δy heuristic), peak boundary / baseline advisories;
  NiceGUI amber strip labeled **Advisory:** (not LOD / not instrument qualification)
- **TeachSpec UVC path** — ingest interface stub → optional live OpenCV UVC
  (`[teachspec]` extra) → NiceGUI live preview `teachspec-ui` (Mock default; port 8082)
- **TeachSpec docs** — USB-cam (UVC) sensor lock, `SAFETY.md`, `BOM_v0.md` skeleton
- **FID/NMR Phase-0 stub** — mock FID→FFT→phase → `Spectrum`; CLI + thin examples walkthrough
- **Public NIST UV-Vis fixtures** — benzene / acetone / naphthalene + tutorial trio
  (log₁₀(ε) honesty preserved)
- **Plot PNG export**, folder waterfall optional **3-D surface**, session load auto-replay of
  pipeline history onto working (raw preserved)
- **Classroom pilot one-pager** — `docs/classroom_pilot_one_pager.md`
- **Release checklist** — `docs/RELEASE_0.2.md` (build / twine check / TestPyPI / PyPI;
  publish is maintainer-run)

### Changed

- Package / module `__version__` → **0.2.0** (`pyproject.toml`, `spectrum_core`, `chemspec`,
  `labrf`, `teachspec`, `fidnmr`)
- `pyproject.toml` — classifiers, keywords, and project URLs (Homepage / Repository / Issues /
  Changelog); confirmed MIT, `requires-python >=3.10`, name `chemspec-workbench`
- README Experimental framing for LabRF / TeachSpec / FID-NMR siblings
- ROADMAP / STATUS — 0.2 Measurement Integrity + TeachSpec UVC marked release-prep Done;
  PyPI publish waiting on credentials

### Fixed

- Fixture reload resets processing pipeline state (UI honesty)
- Various docs polish (fingerprint units, SNR MAD advisory wording, family README honesty)

### Security / packaging

- Dependabot (pip + github-actions); CI `pip-audit` on 3.11 / 3.13
- No secrets in-repo; PyPI upload **not** performed in this release-prep PR

## [0.1.0] — 2026-09

Initial public scaffold: `spectrum_core` + ChemSpec NiceGUI MVP (CSV/JCAMP ingest, peaks,
baseline, overlay, folder waterfall, processing pipeline, session save/load), LabRF mock
monitor, synthetic fixtures, public PNNL/NIST IR ethanol/methanol/toluene, MIT license.

[Unreleased]: https://github.com/Garthnesss/chemspec-workbench/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Garthnesss/chemspec-workbench/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Garthnesss/chemspec-workbench/releases/tag/v0.1.0
