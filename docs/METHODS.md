# Methods note — ChemSpec Workbench

Short description of what the software *computes*. Not a paper. Not compound ID.

## SPC ingest

`ingest_spc` reads Thermo Galactic / GRAMS ``.spc`` **new little-endian (0x4B)**.
Even-X or global TXVALS X; first subfile only. XYXY and old/big-endian raise.
Units from ``fxtype`` / ``fytype`` (nm, cm-1, A, %T when those codes match).

## Peak metrics

`find_peaks` wraps SciPy `find_peaks`. FWHM and area use a **prominence-relative
half-maximum** (`y_half = y_peak - 0.5 P`), matching SciPy `peak_widths`
`rel_height=0.5`. Area is the trapezoid between those bounds. Missing crossings
are NaN. This is geometry on the loaded trace.

## Folder grid / 3-D

`spectra_to_surface` builds `x × series_index × y`. The second axis is
**folder order**, not time. Stack offsets are stripped. Uneven x is linearly
interpolated on the overlap only (no extrapolation).

- Δy vs first = `z - z[0]` (not a derivative).
- Residual vs mean = `z - mean(loaded traces)` (not a solvent blank).
- Ridge tracks = local maxima per series (not assignments).

## Named blank subtract

`subtract_spectra(sample, reference, role="blank")` interpolates the reference
onto the sample x-grid and subtracts. Units must match. Out-of-range x → NaN.
The caller names the blank by passing the spectrum. ChemSpec does not detect
solvent.

## Quant (loaded-trace geometry)

- `derivative_spectrum` — Savitzky–Golay order 1 or 2. `y_unit` unchanged.
- `band_integral` — trapezoid on a user `[x_lo, x_hi]`; optional linear ends.
- `compare_spectra` — RMSE / MAE / Pearson r / cosine on sample x-grid.
- `beer_lambert_c(A, ε, path)` — caller supplies ε and path. No ε library.
- `convert_spectrum_x` — nm ↔ cm-1 via `10^7 / x`.

None of these identify compounds.

## Session identity

`.csw.json` stores `raw_data_hash` (SHA-256 of canonical x‖y) and
`analysis_fingerprint`. Notes and timestamps do not change the fingerprint.

## Citation

See `CITATION.cff`. Public fixtures: `fixtures/public/SOURCES.md`.
