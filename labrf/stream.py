"""Streaming mock IQ frame generator (no UI sleep — unit-testable)."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from labrf.backend import IqSource, MockIqSource
from labrf.fft_spectrum import iq_to_spectrum
from spectrum_core.spectrum import Spectrum


@dataclass
class StreamFrame:
    """One streamed FFT frame plus provenance metadata."""

    spectrum: Spectrum
    frame_index: int
    source_kind: str  # "mock" | "fixture" | "rtlsdr"
    center_hz: float
    sample_rate: float


@dataclass
class MockStreamGenerator:
    """Pull successive mock IQ frames with slight variation between frames.

    Uses ``MockIqSource`` seed stepping (and optional noise/tone jitter) so
    each ``next_frame()`` differs slightly — suitable for waterfall demos
    without a dongle. No timers or sleep; the UI owns scheduling.
    """

    source: IqSource
    n_fft: int = 2048
    window: str = "hann"
    frame_index: int = 0
    source_kind: str = "mock"
    # Optional mild jitter applied only for MockIqSource synthetic path
    noise_jitter: float = 0.01
    tone_amp_jitter: float = 0.05
    _rng: np.random.Generator = field(default_factory=lambda: np.random.default_rng(0))

    def __post_init__(self) -> None:
        if self.n_fft < 8:
            raise ValueError("n_fft must be >= 8")
        if isinstance(self.source, MockIqSource):
            if self.source.fixture_path or self.source._fixture_iq is not None:
                self.source_kind = "fixture"
            else:
                self.source_kind = "mock"
        else:
            self.source_kind = getattr(self.source, "kind", "rtlsdr")

    @property
    def center_hz(self) -> float:
        return float(self.source.center_freq)

    @property
    def sample_rate(self) -> float:
        return float(self.source.sample_rate)

    def reset(self) -> None:
        self.frame_index = 0

    def next_frame(self) -> StreamFrame:
        """Read one IQ block, FFT → Spectrum, bump frame counter.

        For synthetic mock sources, lightly varies noise_std / tone amps by
        regenerating via ``generate_synthetic_iq`` with an advanced seed so
        successive waterfall rows are visibly different.
        """
        from labrf.iq import generate_synthetic_iq

        src = self.source
        if (
            isinstance(src, MockIqSource)
            and src._fixture_iq is None
            and (self.noise_jitter > 0 or self.tone_amp_jitter > 0)
        ):
            # Mild variation around defaults so waterfall is not a static image
            base_noise = 0.05
            noise = max(
                0.0,
                base_noise
                + float(self._rng.normal(0.0, self.noise_jitter)),
            )
            amp0 = max(0.2, 1.0 + float(self._rng.normal(0.0, self.tone_amp_jitter)))
            amp1 = max(0.2, 0.7 + float(self._rng.normal(0.0, self.tone_amp_jitter)))
            seed = src.seed if src.seed is not None else int(self._rng.integers(0, 2**31))
            iq, _meta = generate_synthetic_iq(
                n_samples=self.n_fft,
                sample_rate=src.sample_rate,
                center_freq=src.center_freq,
                tone_amps=(amp0, amp1),
                noise_std=noise,
                seed=seed,
            )
            if src.seed is not None:
                src.seed += 1
        else:
            iq = src.read_samples(self.n_fft)

        kind = self.source_kind
        title = f"RF stream [{kind}] @ {src.center_freq / 1e6:.4f} MHz"
        spec = iq_to_spectrum(
            iq,
            sample_rate=src.sample_rate,
            center_freq=src.center_freq,
            window=self.window,  # type: ignore[arg-type]
            x_unit="MHz",
            y_unit="dB",
            title=title,
            meta={
                "source": kind,
                "frame_index": self.frame_index,
                "streaming": True,
            },
        )
        frame = StreamFrame(
            spectrum=spec,
            frame_index=self.frame_index,
            source_kind=kind,
            center_hz=float(src.center_freq),
            sample_rate=float(src.sample_rate),
        )
        self.frame_index += 1
        return frame


def format_labrf_provenance(
    *,
    source_kind: str,
    center_hz: float,
    sample_rate: float,
    frames: int,
    streaming: bool = False,
    peak_count: int = 0,
    threshold_db: float | None = None,
    event_count: int = 0,
) -> str:
    """One-line provenance strip for LabRF status area."""
    mode = "streaming" if streaming else "idle"
    parts = [
        f"source={source_kind}",
        f"center={center_hz / 1e6:.4f} MHz",
        f"rate={sample_rate / 1e6:.4f} MS/s",
        f"frames={int(frames)}",
        f"mode={mode}",
        f"peaks={int(peak_count)}",
    ]
    if threshold_db is not None:
        parts.append(f"threshold={threshold_db:.1f} dB")
        parts.append(f"events={int(event_count)}")
    return " · ".join(parts)
