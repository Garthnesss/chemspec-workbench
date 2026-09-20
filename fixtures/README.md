# Fixtures (synthetic)

These files are **synthetic** teaching/demo data. They are **not** measured spectra
of real compounds and must never be described as such.

| File | Format | X axis | Y axis | Intended peaks |
|------|--------|--------|--------|----------------|
| `uvvis_synthetic.csv` | CSV | `wavelength_nm` (nm) | `absorbance` → `y_unit=A` | ~280 nm, ~350 nm |
| `ir_synthetic.csv` | CSV | `wavenumber_cm-1` (cm⁻¹) | `intensity` (not %T/A) | ~1700 cm⁻¹, ~2900 cm⁻¹ (weaker ~1450) |
| `uvvis_synthetic.jdx` | JCAMP-DX | NANOMETERS → `nm` | ABSORBANCE → `A` | ~280 nm, ~350 nm |
| `ir_synthetic.dx` | JCAMP-DX | 1/CM → `cm-1` | TRANSMITTANCE (fraction→%T) | dips ~1700, ~2900 cm⁻¹ |
| `waterfall/t0{0,1,2}_synthetic.csv` | CSV folder | `wavelength_nm` | `absorbance` | slight peak drift for stack demo |

CSV files include `#` comment lines and a header row. Use
`spectrum_core.ingest_csv` with column names or indices.

JCAMP files are minimal XYDATA text (no huge binary). Use
`spectrum_core.ingest_jcamp` (MIT [`jcamp`](https://pypi.org/project/jcamp/) package).

Folder waterfall demos: `spectrum_core.folder_waterfall("fixtures/waterfall", ...)`
or the UI **Demo waterfall fixture** button.


CSV `#` comments may include `x_unit=` / `y_unit=` hints. UI `guess_column_mapping` maps absorbance-named columns (`absorbance`, `A`, `AU`, `Abs`, `OD`) to `y_unit=A`; IR intensity stays intensity.

**Honesty:** ChemSpec Workbench does not claim compound identity from these
(or any) spectra in Phase 0.

| `labrf/mock_iq.npz` | NumPy IQ | complex baseband | synthetic tones near 98 MHz (LabRF mock) |

LabRF IQ fixtures: see `fixtures/labrf/README.md`. Synthetic only — not live captures.

