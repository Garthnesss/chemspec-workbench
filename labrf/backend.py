"""RF IQ source protocol + mock backend (hardware optional)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import numpy as np

from labrf.iq import generate_synthetic_iq, load_iq_fixture


@runtime_checkable
class IqSource(Protocol):
    """Thin protocol for IQ backends (mock or RTL-SDR)."""

    @property
    def sample_rate(self) -> float: ...

    @property
    def center_freq(self) -> float: ...

    def configure(self, *, center_freq: float, sample_rate: float) -> None: ...

    def read_samples(self, n: int) -> np.ndarray: ...

    def close(self) -> None: ...


@dataclass
class MockIqSource:
    """Synthetic / fixture IQ source — no dongle required (CI default)."""

    sample_rate: float = 2.048e6
    center_freq: float = 98e6
    seed: int | None = 42
    fixture_path: str | None = None
    _fixture_iq: np.ndarray | None = field(default=None, repr=False)
    _cursor: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        if self.fixture_path:
            iq, meta = load_iq_fixture(self.fixture_path)
            self._fixture_iq = iq
            self.sample_rate = float(meta["sample_rate"])
            self.center_freq = float(meta["center_freq"])

    def configure(self, *, center_freq: float, sample_rate: float) -> None:
        self.center_freq = float(center_freq)
        self.sample_rate = float(sample_rate)
        # Regenerating tones track the new center; drop fixture cursor loop
        if self._fixture_iq is None:
            self.seed = (self.seed or 0) + 1

    def read_samples(self, n: int) -> np.ndarray:
        if n < 1:
            raise ValueError("n must be >= 1")
        if self._fixture_iq is not None:
            iq = self._fixture_iq
            if len(iq) >= n:
                # Loop through fixture
                out = np.empty(n, dtype=np.complex128)
                for i in range(n):
                    out[i] = iq[self._cursor % len(iq)]
                    self._cursor += 1
                return out
            # Pad by regenerating if fixture shorter than request
            reps = int(np.ceil(n / len(iq)))
            tiled = np.tile(iq, reps)[:n]
            return tiled.astype(np.complex128)

        iq, _meta = generate_synthetic_iq(
            n_samples=n,
            sample_rate=self.sample_rate,
            center_freq=self.center_freq,
            seed=self.seed,
        )
        if self.seed is not None:
            self.seed += 1
        return iq

    def close(self) -> None:
        return None


def open_rtlsdr_source(
    *,
    center_freq: float = 98e6,
    sample_rate: float = 2.048e6,
    gain: str | float = "auto",
) -> IqSource:
    """Open optional RTL-SDR backend (requires ``[labrf]`` / ``[rtlsdr]`` extra)."""
    from labrf.rtlsdr_adapter import RtlSdrSource

    return RtlSdrSource(
        center_freq=center_freq,
        sample_rate=sample_rate,
        gain=gain,
    )
