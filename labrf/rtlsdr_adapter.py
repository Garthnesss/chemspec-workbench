"""Optional RTL-SDR adapter (receive-only). Import only when extra installed."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

_MISSING_MSG = (
    "RTL-SDR support requires optional deps. Install with:\n"
    '  pip install -e ".[labrf]"\n'
    "or:\n"
    '  pip install -e ".[rtlsdr]"\n'
    "Hardware is never required for CI / mock mode "
    "(use labrf.backend.MockIqSource)."
)


def _import_rtlsdr() -> Any:
    try:
        from rtlsdr import RtlSdr  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - exercised in missing-extra test
        raise ImportError(_MISSING_MSG) from exc
    return RtlSdr


@dataclass
class RtlSdrSource:
    """Thin receive-only wrapper around pyrtlsdr.

    Only imports ``rtlsdr`` when constructed. Do **not** use in CI without hardware.
    """

    center_freq: float = 98e6
    sample_rate: float = 2.048e6
    gain: str | float = "auto"
    _sdr: Any = field(default=None, repr=False, init=False)

    def __post_init__(self) -> None:
        RtlSdr = _import_rtlsdr()
        sdr = RtlSdr()
        sdr.sample_rate = float(self.sample_rate)
        sdr.center_freq = float(self.center_freq)
        sdr.gain = self.gain
        self._sdr = sdr

    def configure(self, *, center_freq: float, sample_rate: float) -> None:
        if self._sdr is None:
            raise RuntimeError("RTL-SDR device is closed")
        self.center_freq = float(center_freq)
        self.sample_rate = float(sample_rate)
        self._sdr.sample_rate = self.sample_rate
        self._sdr.center_freq = self.center_freq

    def read_samples(self, n: int) -> np.ndarray:
        if self._sdr is None:
            raise RuntimeError("RTL-SDR device is closed")
        samples = self._sdr.read_samples(int(n))
        return np.asarray(samples, dtype=np.complex128)

    def close(self) -> None:
        if self._sdr is not None:
            try:
                self._sdr.close()
            finally:
                self._sdr = None
