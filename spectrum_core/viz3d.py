"""3-D surface grid from a list of 1-D spectra.

Display-only helper. The second axis is **series index** (folder order),
not time. Stack y-offsets used by 2-D waterfall are stripped so surface
height is the measured y, not a display shift.

Does not identify compounds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from spectrum_core.overlay import overlay
from spectrum_core.spectrum import Spectrum, XUnit, YUnit

_MAX_X_BINS = 2048


@dataclass(frozen=True)
class SurfaceGrid:
    """Regular grid ready for a surface / mesh plot.

    Attributes
    ----------
    x :
        Shared spectral axis, shape ``(n_x,)``.
    series :
        Series indices ``0 .. n_series-1``, shape ``(n_series,)``.
        **Not** a time axis.
    z :
        Intensity / absorbance / %T on the shared grid,
        shape ``(n_series, n_x)``.
    series_kind :
        Always ``\"series_index\"`` in this module — do not label as time.
    resampled :
        True when traces were interpolated onto a shared x grid.
    """

    x: np.ndarray
    series: np.ndarray
    z: np.ndarray
    x_unit: XUnit
    y_unit: YUnit
    titles: tuple[str, ...]
    series_kind: str = "series_index"
    resampled: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", np.asarray(self.x, dtype=float))
        object.__setattr__(self, "series", np.asarray(self.series, dtype=float))
        object.__setattr__(self, "z", np.asarray(self.z, dtype=float))
        if self.x.ndim != 1 or self.series.ndim != 1:
            raise ValueError("x and series must be 1-D")
        if self.z.shape != (len(self.series), len(self.x)):
            raise ValueError(
                f"z shape {self.z.shape} != "
                f"({len(self.series)}, {len(self.x)})"
            )
        if self.series_kind != "series_index":
            raise ValueError(
                "series_kind must be 'series_index' "
                "(folder order is not a time axis)"
            )


def _raw_y(spec: Spectrum) -> np.ndarray:
    """Undo 2-D waterfall stack offset if present."""
    offset = float(spec.meta.get("stack_offset", 0.0) or 0.0)
    return np.asarray(spec.y, dtype=float) - offset


def _same_x(spectra: list[Spectrum]) -> bool:
    x0 = spectra[0].x
    for s in spectra[1:]:
        if len(s.x) != len(x0):
            return False
        if not np.allclose(s.x, x0, rtol=1e-9, atol=1e-12, equal_nan=False):
            return False
    return True


def _interp_to_grid(spec: Spectrum, grid: np.ndarray) -> np.ndarray:
    """Linear interpolate ``spec.y`` (stack-offset stripped) onto ``grid``.

    ``np.interp`` needs an increasing sample axis; IR traces are often
    descending. Out-of-range grid points become NaN (no extrapolation).
    """
    x = np.asarray(spec.x, dtype=float)
    y = _raw_y(spec)
    order = np.argsort(x)
    xs = x[order]
    ys = y[order]
    if len(xs) > 1:
        uniq = np.concatenate(([True], np.diff(xs) != 0))
        xs = xs[uniq]
        ys = ys[uniq]
    out = np.interp(grid, xs, ys, left=np.nan, right=np.nan)
    return out


def spectra_to_surface(
    spectra: list[Spectrum],
    *,
    n_x: int | None = None,
) -> SurfaceGrid:
    """Build a ``SurfaceGrid`` from two or more spectra.

    Matching ``x_unit`` is required (same rule as ``overlay`` / ``stack``).
    Matching ``y_unit`` is required so surface height stays honest.

    Parameters
    ----------
    spectra :
        Folder traces in display order. Stack offsets in ``meta`` are
        stripped.
    n_x :
        Optional shared-grid length when resampling. Default is the
        longest trace, capped at 2048.
    """
    if len(spectra) < 2:
        raise ValueError("3-D surface needs at least two spectra")

    aligned = overlay(spectra)
    y0 = aligned[0].y_unit
    for i, s in enumerate(aligned):
        if s.y_unit != y0:
            raise ValueError(
                f"spectrum[{i}] y_unit={s.y_unit!r} != {y0!r}; "
                "3-D surface requires matching y units"
            )

    titles = tuple(s.title or f"trace_{i}" for i, s in enumerate(aligned))

    if _same_x(aligned):
        z = np.vstack([_raw_y(s) for s in aligned])
        return SurfaceGrid(
            x=aligned[0].x.copy(),
            series=np.arange(len(aligned), dtype=float),
            z=z,
            x_unit=aligned[0].x_unit,
            y_unit=y0,
            titles=titles,
            resampled=False,
            meta={"n_series": len(aligned), "honesty": "series_index_not_time"},
        )

    lo = -np.inf
    hi = np.inf
    for s in aligned:
        xs = np.asarray(s.x, dtype=float)
        lo = max(lo, float(np.nanmin(xs)))
        hi = min(hi, float(np.nanmax(xs)))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        raise ValueError("spectra have no overlapping x range for a 3-D grid")

    if n_x is None:
        n_x = min(_MAX_X_BINS, max(len(s.x) for s in aligned))
    n_x = max(2, int(n_x))
    grid = np.linspace(lo, hi, n_x)
    z = np.vstack([_interp_to_grid(s, grid) for s in aligned])
    return SurfaceGrid(
        x=grid,
        series=np.arange(len(aligned), dtype=float),
        z=z,
        x_unit=aligned[0].x_unit,
        y_unit=y0,
        titles=titles,
        resampled=True,
        meta={
            "n_series": len(aligned),
            "honesty": "series_index_not_time",
            "x_overlap": [lo, hi],
        },
    )
