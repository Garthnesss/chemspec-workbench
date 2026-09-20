# Ingest edge-case fixtures (synthetic)

Synthetic CSV/JCAMP snippets for ugly real-world ingest cases. **Not** measured
spectra of real compounds.

| File | Case |
|------|------|
| `descending_x_ir.csv` | Descending / reversed x (common IR cm⁻¹) |
| `duplicate_x.csv` | Duplicate x values |
| `uneven_spacing.csv` | Uneven Δx |
| `nan_inf_y.csv` | NaN / Inf in y (skip policy) |
| `semicolon_delim.csv` | Semicolon delimiter |
| `tab_delim.tsv` | Tab delimiter |
| `quoted_fields.csv` | Quoted CSV fields (commas inside quotes) |
| `missing_extra_cols.csv` | Missing values + extra columns |
| `percent_t_header.csv` | `%T` / transmittance header |
| `absorbance_header.csv` | Absorbance header |
| `empty.csv` | Empty file → clear error |
| `bad_minimal.jdx` | Bad / empty JCAMP → clear error |

Policy notes live in `spectrum_core.ingest` module docs and SPEC.md.
