# Fixtures (synthetic)

These files are **synthetic** teaching/demo data. They are **not** measured spectra
of real compounds and must never be described as such.

| File | Format | X axis | Y axis | Intended peaks |
|------|--------|--------|--------|----------------|
| `uvvis_synthetic.csv` | CSV | `wavelength_nm` (nm) | `absorbance` (A) | ~280 nm, ~350 nm |
| `ir_synthetic.csv` | CSV | `wavenumber_cm-1` (cm⁻¹) | `intensity` | ~1700 cm⁻¹, ~2900 cm⁻¹ (weaker ~1450) |
| `uvvis_synthetic.jdx` | JCAMP-DX | NANOMETERS → `nm` | ABSORBANCE → `A` | ~280 nm, ~350 nm |
| `ir_synthetic.dx` | JCAMP-DX | 1/CM → `cm-1` | TRANSMITTANCE (fraction→%T) | dips ~1700, ~2900 cm⁻¹ |
| `waterfall/t0{0,1,2}_synthetic.csv` | CSV folder | `wavelength_nm` | `absorbance` | slight peak drift for stack demo |

CSV files include `#` comment lines and a header row. Use
`spectrum_core.ingest_csv` with column names or indices.

JCAMP files are minimal XYDATA text (no huge binary). Use
`spectrum_core.ingest_jcamp` (MIT [`jcamp`](https://pypi.org/project/jcamp/) package).

Folder waterfall demos: `spectrum_core.folder_waterfall("fixtures/waterfall", ...)`
or the UI **Demo waterfall fixture** button.

**Honesty:** ChemSpec Workbench does not claim compound identity from these
(or any) spectra in Phase 0.
