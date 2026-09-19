"""Peak detection helpers (scipy.signal.find_peaks wrapper)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks as _scipy_find_peaks

from spectrum_core.spectrum import Spectrum


@dataclass(frozen=True)
class Peak:
    """A detected peak location on a spectrum."""

    index: int
    x: float
    y: float
    prominence: float


def find_peaks(
    spectrum: Spectrum,
    *,
    prominence: float | None = None,
    height: float | None = None,
    distance: int | None = None,
    width: float | None = None,
) -> list[Peak]:
    """Find peaks on ``spectrum.y`` using ``scipy.signal.find_peaks``.

    ``prominence`` defaults to 10% of the y-range when not provided, so
    fixtures with clear Gaussians are found without tuning.

    Returns peaks sorted by descending prominence.
    """
    y = spectrum.y
    if prominence is None:
        y_range = float(np.nanmax(y) - np.nanmin(y))
        prominence = 0.1 * y_range if y_range > 0 else None

    kwargs: dict = {}
    if prominence is not None:
        kwargs["prominence"] = prominence
    if height is not None:
        kwargs["height"] = height
    if distance is not None:
        kwargs["distance"] = distance
    if width is not None:
        kwargs["width"] = width

    indices, props = _scipy_find_peaks(y, **kwargs)
    prominences = props.get("prominences")
    peaks: list[Peak] = []
    for i, idx in enumerate(indices):
        prom = float(prominences[i]) if prominences is not None else 0.0
        peaks.append(
            Peak(
                index=int(idx),
                x=float(spectrum.x[idx]),
                y=float(spectrum.y[idx]),
                prominence=prom,
            )
        )
    peaks.sort(key=lambda p: p.prominence, reverse=True)
    return peaks
