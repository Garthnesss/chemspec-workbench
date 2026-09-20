"""Waterfall buffer: stack successive RF power spectra for heatmap / stack view."""

from __future__ import annotations

from collections import deque
from typing import Iterable

import numpy as np

from spectrum_core.overlay import stack
from spectrum_core.spectrum import Spectrum


class WaterfallBuffer:
    """Ring buffer of successive ``Spectrum`` frames (same x-axis expected).

    Reuses ``spectrum_core.stack`` for offset traces; also exposes a 2-D
    power matrix for heatmap display.
    """

    def __init__(self, maxlen: int = 64) -> None:
        if maxlen < 1:
            raise ValueError("maxlen must be >= 1")
        self.maxlen = int(maxlen)
        self._frames: deque[Spectrum] = deque(maxlen=self.maxlen)

    def __len__(self) -> int:
        return len(self._frames)

    def clear(self) -> None:
        self._frames.clear()

    def push(self, spectrum: Spectrum) -> bool:
        """Append a spectrum frame (oldest dropped when full).

        Returns ``True`` if the buffer was cleared first because the new
        frame's frequency axis differs (unit, length, or x values). That
        keeps heatmap x-labels honest after a retune mid-stream.
        """
        reset = False
        if self._frames:
            first = self._frames[0]
            axis_ok = (
                spectrum.x_unit == first.x_unit
                and len(spectrum.x) == len(first.x)
                and np.allclose(spectrum.x, first.x, rtol=0.0, atol=1e-9, equal_nan=True)
            )
            if not axis_ok:
                self._frames.clear()
                reset = True
        self._frames.append(spectrum)
        return reset

    def extend(self, spectra: Iterable[Spectrum]) -> None:
        for s in spectra:
            self.push(s)

    @property
    def frames(self) -> list[Spectrum]:
        return list(self._frames)

    def as_stacked(self, *, offset: float | None = None) -> list[Spectrum]:
        """Return ``stack(...)`` offset traces (ChemSpec-style waterfall)."""
        return stack(self.frames, offset=offset)

    def as_matrix(self) -> tuple[np.ndarray, np.ndarray]:
        """Return ``(x, Z)`` where ``Z`` is shape ``(n_frames, n_bins)`` (oldest first).

        ``x`` is taken from the newest frame's frequency axis.
        """
        if not self._frames:
            return np.asarray([], dtype=float), np.zeros((0, 0), dtype=float)
        x = self._frames[-1].x.copy()
        z = np.vstack([f.y for f in self._frames])
        return x, z
