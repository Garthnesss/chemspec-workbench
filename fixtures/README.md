# Fixtures (synthetic)

These CSVs are **synthetic** teaching/demo data. They are **not** measured spectra
of real compounds and must never be described as such.

| File | X axis | Y axis | Intended peaks |
|------|--------|--------|----------------|
| `uvvis_synthetic.csv` | `wavelength_nm` (nm) | `absorbance` (A) | ~280 nm, ~350 nm |
| `ir_synthetic.csv` | `wavenumber_cm-1` (cm⁻¹) | `intensity` | ~1700 cm⁻¹, ~2900 cm⁻¹ (weaker ~1450) |

Both files include `#` comment lines and a header row. Use
`spectrum_core.ingest_csv` with column names or indices.

**Honesty:** ChemSpec Workbench does not claim compound identity from these
(or any) spectra in Phase 0.
