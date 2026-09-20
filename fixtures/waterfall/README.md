# Waterfall demo folder (synthetic)

Three synthetic UV-Vis absorbance CSVs for folder-waterfall / stack demos.

| File | Role |
|------|------|
| `t00_synthetic.csv` | First trace (sorts first by name) |
| `t01_synthetic.csv` | Slight peak drift |
| `t02_synthetic.csv` | Further drift |

**Not real compounds.** Filenames sort as `t00`, `t01`, `t02` (case-insensitive name order).

## How to load

**ChemSpec UI:** section **4 · Folder waterfall** → **Demo waterfall fixture**, or
set the folder path to this directory and **Load folder**.

**Python:**

```python
from spectrum_core import folder_waterfall

stacked = folder_waterfall(
    "fixtures/waterfall",
    x_col="wavelength_nm",
    y_col="absorbance",
    x_unit="nm",
    y_unit="A",
    offset=1.0,
)
```

Stack offsets are for display only — there is no true time-axis metadata from filenames
beyond sort-by-name / mtime. See root README **Folder waterfall** and **Quick demo**.
