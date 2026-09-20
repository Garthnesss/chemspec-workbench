"""Peak-hold / max-hold tracker for RF power spectra (receive-only demos).

Educational mock-path helper: accumulates the per-bin maximum across successive
frames so transient tones remain visible. Not a hardware-verified measurement
claim and not chemical identification.
"""

from __future__ import annotations

import numpy as np

from spectrum_core.spectrum import Spectrum


class PeakHoldTracker:
    """Track per-bin max (peak-hold / max-hold) across power-spectrum frames.

    When the frequency axis changes (retune), the hold resets so labels stay
    honest. Disabled by default — callers must set ``enabled=True``.
    """

    def __init__(self, *, enabled: bool = False) -> None:
        self.enabled = bool(enabled)
        self._held: Spectrum | None = None
        self.n_updates: int = 0

    def __len__(self) -> int:
        return 0 if self._held is None else len(self._held)

    @property
    def held(self) -> Spectrum | None:
        """Current held spectrum, or ``None`` if empty / never updated."""
        return self._held

    def clear(self) -> None:
        self._held = None
        self.n_updates = 0

    def _axis_matches(self, spectrum: Spectrum) -> bool:
        if self._held is None:
            return True
        held = self._held
        return (
            spectrum.x_unit == held.x_unit
            and spectrum.y_unit == held.y_unit
            and len(spectrum.x) == len(held.x)
            and np.allclose(spectrum.x, held.x, rtol=0.0, atol=1e-9, equal_nan=True)
        )

    def update(self, spectrum: Spectrum) -> Spectrum | None:
        """Fold ``spectrum`` into the hold when enabled.

        Returns the current held spectrum when enabled (after update), else
        ``None``. Axis mismatch clears the prior hold first.
        """
        if not self.enabled:
            return None
        if self._held is not None and not self._axis_matches(spectrum):
            self.clear()
        if self._held is None:
            self._held = spectrum.copy()
            title = spectrum.title or "RF power spectrum"
            if "peak-hold" not in title.lower() and "max-hold" not in title.lower():
                self._held.title = f"{title} (peak-hold / max-hold)"
            self._held.meta = {
                **dict(spectrum.meta),
                "peak_hold": True,
                "max_hold": True,
                "peak_hold_updates": 1,
            }
            self.n_updates = 1
            return self._held
        y = np.maximum(self._held.y, spectrum.y)
        self._held = self._held.with_y(y, title=self._held.title)
        self.n_updates += 1
        self._held.meta = {
            **dict(self._held.meta),
            "peak_hold": True,
            "max_hold": True,
            "peak_hold_updates": int(self.n_updates),
        }
        return self._held
