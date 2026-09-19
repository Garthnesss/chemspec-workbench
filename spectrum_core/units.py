"""Absorbance ↔ percent transmittance conversion helpers.

Formulas (Beer–Lambert / standard spectrophotometry):

* ``percent_T = 100 * 10**(-A)``
* ``A = -log10(percent_T / 100)``

Limits (documented, enforced)
-----------------------------
* Only ``y_unit`` of ``"A"`` or ``"percent_T"`` may convert; ``"intensity"``
  raises ``ValueError`` (no physical mapping without calibration).
* Absorbance must be finite; non-finite → ``nan`` in output (no raise).
* Percent transmittance must be **strictly positive**; ``<= 0`` → ``nan``
  (log undefined). Values ``> 100`` are allowed (noisy / overshoot data)
  but noted in ``meta`` when present.
* Conversion returns a **new** ``Spectrum``; x / title preserved; ``meta``
  gains ``y_unit_converted_from`` and optional ``conversion_notes``.
"""

from __future__ import annotations

import numpy as np

from spectrum_core.spectrum import Spectrum, YUnit


def absorbance_to_percent_t(a: np.ndarray | float) -> np.ndarray:
    """Convert absorbance to percent transmittance: ``%T = 100 * 10**(-A)``.

    Non-finite absorbance values become ``nan``. Always returns an ``ndarray``.
    """
    arr = np.asarray(a, dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    ok = np.isfinite(arr)
    out[ok] = 100.0 * np.power(10.0, -arr[ok])
    return out


def percent_t_to_absorbance(percent_t: np.ndarray | float) -> np.ndarray:
    """Convert percent transmittance to absorbance: ``A = -log10(%T / 100)``.

    Non-finite or ``<= 0`` percent_T values become ``nan``. Always returns
    an ``ndarray``.
    """
    arr = np.asarray(percent_t, dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    ok = np.isfinite(arr) & (arr > 0.0)
    out[ok] = -np.log10(arr[ok] / 100.0)
    return out


def convert_spectrum_y(spectrum: Spectrum, target: YUnit) -> Spectrum:
    """Return a copy of ``spectrum`` with ``y`` converted to ``target`` y-unit.

    Parameters
    ----------
    spectrum :
        Input spectrum (``y_unit`` must be ``A`` or ``percent_T``).
    target :
        Desired ``y_unit``: ``"A"`` or ``"percent_T"``.

    Raises
    ------
    ValueError
        If ``spectrum.y_unit`` or ``target`` is ``intensity``, or if
        ``target`` is not a supported conversion endpoint.
    """
    if target not in ("A", "percent_T"):
        raise ValueError(
            f"convert_spectrum_y target must be 'A' or 'percent_T', got {target!r}"
        )
    src = spectrum.y_unit
    if src == "intensity":
        raise ValueError(
            "cannot convert y_unit='intensity' ↔ A/%T without calibration; "
            "load or map data as absorbance or percent transmittance first"
        )
    if src not in ("A", "percent_T"):
        raise ValueError(f"unsupported source y_unit: {src!r}")
    if src == target:
        return spectrum.copy()

    notes: list[str] = []
    if src == "A" and target == "percent_T":
        y_new = absorbance_to_percent_t(spectrum.y)
        if not np.all(np.isfinite(spectrum.y)):
            notes.append("non-finite absorbance → nan %T")
    else:  # percent_T → A
        y_new = percent_t_to_absorbance(spectrum.y)
        y_arr = np.asarray(spectrum.y, dtype=float)
        if np.any(np.isfinite(y_arr) & (y_arr <= 0.0)):
            notes.append("percent_T <= 0 → nan absorbance (log undefined)")
        if np.any(np.isfinite(y_arr) & (y_arr > 100.0)):
            notes.append("percent_T > 100 present (allowed; noisy/overshoot)")

    out = Spectrum(
        x=spectrum.x.copy(),
        y=np.asarray(y_new, dtype=float),
        x_unit=spectrum.x_unit,
        y_unit=target,
        title=spectrum.title,
        meta={
            **spectrum.meta,
            "y_unit_converted_from": src,
        },
    )
    if notes:
        out.meta["conversion_notes"] = notes
    return out


def can_convert_y(y_unit: YUnit) -> bool:
    """True when ``y_unit`` supports A ↔ %T conversion."""
    return y_unit in ("A", "percent_T")
