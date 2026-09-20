# 3-D surface (display only)

`spectrum_core.viz3d.spectra_to_surface` turns a folder of spectra into a
`SurfaceGrid` (`x` × series-index × y).

## Honesty

- The second axis is **series index** (folder order / name or mtime sort).
  It is **not** a time axis.
- 2-D waterfall `stack_offset` values are stripped so surface height is
  measured y (A / %T / intensity), not a display shift.
- Needs at least two traces, matching `x_unit` and `y_unit`.
- Uneven x grids are interpolated on the overlapping range only.
- This does **not** identify compounds.

## Python

```python
from spectrum_core import folder_waterfall, spectra_to_surface

stacked = folder_waterfall(
    "fixtures/waterfall",
    x_col="wavelength_nm",
    y_col="absorbance",
    x_unit="nm",
    y_unit="A",
)
grid = spectra_to_surface(stacked)
# grid.x, grid.series, grid.z, grid.series_kind == "series_index"
```

## NiceGUI

`chemspec.plot3d.build_surface_figure(traces, xlabel, ylabel)` builds a
Plotly `Surface` (requires `pip install -e ".[ui]"`).

Wired from section **4 · Folder waterfall**: checkbox sets `state.view_3d`
and `_build_figure` swaps to the surface when a waterfall with ≥2 traces is
loaded (disabled / warn caption if fewer). Series index ≠ time; no compound ID.
