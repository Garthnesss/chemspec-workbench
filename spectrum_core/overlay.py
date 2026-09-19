"""Helpers for overlay / stack of multiple spectra."""

from __future__ import annotations

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
