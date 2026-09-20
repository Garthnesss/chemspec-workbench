# Changelog

All notable changes to **chemspec-workbench** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Quant layer** — SG derivative (pipeline step), user-window band integral,
  compare (RMSE/MAE/Pearson/cosine), nm↔cm-1, Beer–Lambert with *user* ε and path
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
