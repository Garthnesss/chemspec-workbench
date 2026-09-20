"""FID container: complex time-domain signal + NMR metadata.

Phase 0 educational stub — synthetic / fixture paths only. Not a live
spectrometer driver and not compound identification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class FID:
    """One free-induction decay (complex) with acquisition metadata.

    ``signal`` is complex baseband relative to the carrier. ``sw_hz`` is the
    spectral width (Hz); dwell ≈ ``1/sw_hz`` for ``npts`` samples covering
    time ``npts/sw_hz`` (digital NMR convention used in this stub).
    """

    signal: np.ndarray
    sw_hz: float
    obs_mhz: float
    ref_ppm: float = 0.0
    nucleus: str = "1H"
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.signal = np.asarray(self.signal)
        if self.signal.ndim != 1:
            raise ValueError("signal must be 1-D")
        if self.signal.size < 8:
            raise ValueError("signal length must be >= 8")
        if not np.iscomplexobj(self.signal):
            raise ValueError("signal must be complex")
        if float(self.sw_hz) <= 0:
            raise ValueError("sw_hz must be positive")
        if float(self.obs_mhz) <= 0:
            raise ValueError("obs_mhz must be positive")
        self.sw_hz = float(self.sw_hz)
        self.obs_mhz = float(self.obs_mhz)
        self.ref_ppm = float(self.ref_ppm)
        self.nucleus = str(self.nucleus)

    @property
    def npts(self) -> int:
        return int(self.signal.size)

    @property
    def dwell_s(self) -> float:
        """Seconds per sample (1 / spectral width)."""
        return 1.0 / self.sw_hz

    def time_axis_s(self) -> np.ndarray:
        """Acquisition time axis in seconds, length ``npts``."""
        return np.arange(self.npts, dtype=float) * self.dwell_s
