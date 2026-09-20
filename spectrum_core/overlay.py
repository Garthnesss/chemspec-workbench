"""Helpers for overlay / stack of multiple spectra."""

from __future__ import annotations

import numpy as np

from spectrum_core.errors import ProcessingError
from spectrum_core.spectrum import Spectrum


def overlay(spectra: list[Spectrum]) -> list[Spectrum]:
    """Return spectra as an overlay set (same y scale, no offset).

    Validates that all share the same ``x_unit``. Does not resample axes.
    """
    if not spectra:
        return []
    x_unit = spectra[0].x_unit
    for i, s in enumerate(spectra):
        if s.x_unit != x_unit:
            raise ValueError(
                f"spectrum[{i}] x_unit={s.x_unit!r} != {x_unit!r}; "
                "overlay requires matching x units"
            )
    return list(spectra)


def stack(
    spectra: list[Spectrum],
    *,
    offset: float | None = None,
) -> list[Spectrum]:
    """Return spectra offset in y for a stacked / waterfall-style view.

    Parameters
    ----------
    spectra :
        Input list (order preserved; first at bottom / offset 0).
    offset :
        Constant y offset between successive traces. If None, uses
        ``0.1 * max(peak-to-peak of each spectrum)`` (or 1.0 if empty range).
    """
    overlaid = overlay(spectra)
    if not overlaid:
        return []

    if offset is None:
        ranges = []
        for s in overlaid:
            r = float(s.y.max() - s.y.min()) if len(s.y) else 0.0
            ranges.append(r)
        span = max(ranges) if ranges else 0.0
        offset = 0.1 * span if span > 0 else 1.0

    stacked: list[Spectrum] = []
    for i, s in enumerate(overlaid):
        shifted = s.with_y(
            s.y + i * offset,
            title=s.title or f"trace_{i}",
        )
        shifted.meta = {**s.meta, "stack_index": i, "stack_offset": i * offset}
        stacked.append(shifted)
    return stacked


def subtract_spectra(
    sample: Spectrum,
    reference: Spectrum,
    *,
    role: str = "blank",
) -> Spectrum:
    """Return ``sample.y - interp(reference)`` on the sample x-grid.

    ``role`` is a *user label* only (``blank`` or ``reference``). ChemSpec
    does not detect a solvent or background. Matching ``x_unit`` and
    ``y_unit`` required. No extrapolation: points outside the reference
    x-range become NaN.

    Not compound identification.
    """
    label = (role or "blank").strip().lower()
    if label not in {"blank", "reference"}:
        raise ProcessingError(
            "subtract_spectra: role must be 'blank' or 'reference' "
            f"(got {role!r}); this is a user label, not auto-detection"
        )
    if sample.x_unit != reference.x_unit:
        raise ProcessingError(
            f"subtract_spectra: x_unit mismatch "
            f"{sample.x_unit!r} vs {reference.x_unit!r}"
        )
    if sample.y_unit != reference.y_unit:
        raise ProcessingError(
            f"subtract_spectra: y_unit mismatch "
            f"{sample.y_unit!r} vs {reference.y_unit!r}"
        )
    sx = np.asarray(sample.x, dtype=float)
    rx = np.asarray(reference.x, dtype=float)
    ry = np.asarray(reference.y, dtype=float)
    order = np.argsort(rx)
    rx = rx[order]
    ry = ry[order]
    if len(rx) > 1:
        uniq = np.concatenate(([True], np.diff(rx) != 0))
        rx = rx[uniq]
        ry = ry[uniq]
    if rx.size < 2:
        raise ProcessingError(
            "subtract_spectra: reference needs at least two unique x points"
        )
    interp = np.interp(sx, rx, ry, left=np.nan, right=np.nan)
    out = sample.with_y(
        np.asarray(sample.y, dtype=float) - interp,
        title=(sample.title + f" (−{label})").strip(),
    )
    out.meta = {
        **sample.meta,
        "subtract_role": label,
        "subtract_reference_title": reference.title or "",
        "subtract_resampled": not (
            len(rx) == len(sx) and np.allclose(rx, np.sort(sx), rtol=1e-9, atol=1e-12)
        ),
        "honesty": "user_named_blank_or_reference_not_auto_detected",
    }
    return out
