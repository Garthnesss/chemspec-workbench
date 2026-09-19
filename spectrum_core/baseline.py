"""Simple polynomial baseline correction."""

from __future__ import annotations

import numpy as np

from spectrum_core.spectrum import Spectrum


def baseline_polynomial(
    spectrum: Spectrum,
    *,
    degree: int = 2,
    mask: np.ndarray | None = None,
) -> Spectrum:
    """Fit a polynomial to ``spectrum`` and return continuum-subtracted copy.

    Parameters
    ----------
    spectrum :
        Input spectrum.
    degree :
        Polynomial degree (default 2).
    mask :
        Optional boolean mask of points used for the fit (True = use).
        When None, all finite points are used.

    Returns
    -------
    Spectrum
        Same x / units; y is original minus fitted baseline.
        Fitted baseline is stored in ``meta['baseline']``.
    """
    if degree < 0:
        raise ValueError("degree must be >= 0")

    x = spectrum.x
    y = spectrum.y
    finite = np.isfinite(x) & np.isfinite(y)
    if mask is not None:
        mask = np.asarray(mask, dtype=bool)
        if mask.shape != y.shape:
            raise ValueError("mask shape must match y")
        use = finite & mask
    else:
        use = finite

    if int(np.count_nonzero(use)) <= degree:
        raise ValueError(
            f"need more than {degree} points to fit degree-{degree} baseline"
        )

    coeffs = np.polyfit(x[use], y[use], degree)
    baseline = np.polyval(coeffs, x)
    corrected = spectrum.with_y(
        y - baseline,
        title=(spectrum.title + " (baseline corrected)").strip(),
    )
    corrected.meta = {
        **spectrum.meta,
        "baseline": baseline,
        "baseline_degree": degree,
        "baseline_coeffs": coeffs,
    }
    return corrected
