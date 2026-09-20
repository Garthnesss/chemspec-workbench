"""Synthetic 1H-like FIDs for demos and pytest.

Labeled **synthetic** — not a real magnet acquisition and not compound ID.
Peak positions are teaching offsets (ppm) chosen for a clear multi-line demo.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from fidnmr.fid import FID

# Approximate teaching chemical-shift offsets (ppm) for a synthetic multiplet demo.
# Not a claim that any real sample was measured.
DEFAULT_TEACHING_PEAKS_PPM: tuple[float, ...] = (0.0, 1.2, 2.1, 3.5, 7.2)


def generate_mock_fid(
    npts: int = 2048,
    *,
    sw_hz: float = 8000.0,  # ±10 ppm at 400 MHz
    obs_mhz: float = 400.0,
    ref_ppm: float = 0.0,
    peaks_ppm: Sequence[float] | None = None,
    amplitudes: Sequence[float] | None = None,
    t2_s: float = 0.4,
    noise_std: float = 0.02,
    ph0_deg: float = 0.0,
    seed: int | None = 42,
    nucleus: str = "1H",
) -> tuple[FID, dict]:
    """Generate a synthetic complex FID from Lorentzian-like decaying tones.

    Each peak at ``δ`` ppm is placed at carrier-relative frequency
    ``f_hz = (δ - ref_ppm) * obs_mhz`` (inverse of ``hz_to_ppm``).

    Returns ``(fid, truth_meta)`` with generating peak list for tests.
    """
    if npts < 8:
        raise ValueError("npts must be >= 8")
    if sw_hz <= 0 or obs_mhz <= 0:
        raise ValueError("sw_hz and obs_mhz must be positive")
    if t2_s <= 0:
        raise ValueError("t2_s must be positive")

    peaks = list(DEFAULT_TEACHING_PEAKS_PPM if peaks_ppm is None else peaks_ppm)
    if not peaks:
        raise ValueError("peaks_ppm must be non-empty")
    if amplitudes is None:
        amps = [1.0] * len(peaks)
    else:
        amps = [float(a) for a in amplitudes]
        if len(amps) != len(peaks):
            raise ValueError("amplitudes length must match peaks_ppm")

    dwell = 1.0 / float(sw_hz)
    t = np.arange(npts, dtype=float) * dwell
    signal = np.zeros(npts, dtype=np.complex128)
    peak_freqs_hz: list[float] = []

    ph0 = np.deg2rad(float(ph0_deg))
    for ppm, amp in zip(peaks, amps):
        f_hz = (float(ppm) - float(ref_ppm)) * float(obs_mhz)
        peak_freqs_hz.append(f_hz)
        # Decaying complex exponential (Lorentzian after FFT)
        signal += amp * np.exp(1j * (2.0 * np.pi * f_hz * t + ph0)) * np.exp(
            -t / float(t2_s)
        )

    if noise_std > 0:
        rng = np.random.default_rng(seed)
        noise = rng.normal(0.0, float(noise_std), npts) + 1j * rng.normal(
            0.0, float(noise_std), npts
        )
        signal = signal + noise

    meta = {
        "synthetic": True,
        "source": "fidnmr.mock_source.generate_mock_fid",
        "title": "Synthetic 1H-like FID (not a real acquisition)",
        "npts": int(npts),
        "sw_hz": float(sw_hz),
        "obs_mhz": float(obs_mhz),
        "ref_ppm": float(ref_ppm),
        "peaks_ppm": [float(p) for p in peaks],
        "amplitudes": amps,
        "t2_s": float(t2_s),
        "noise_std": float(noise_std),
        "ph0_deg": float(ph0_deg),
        "seed": seed,
        "nucleus": nucleus,
        "disclaimer": (
            "Synthetic educational mock — not hardware-verified; "
            "not compound identification."
        ),
    }
    truth = {
        "peaks_ppm": [float(p) for p in peaks],
        "peak_freqs_hz": peak_freqs_hz,
        "sw_hz": float(sw_hz),
        "obs_mhz": float(obs_mhz),
        "ref_ppm": float(ref_ppm),
    }
    fid = FID(
        signal=signal,
        sw_hz=float(sw_hz),
        obs_mhz=float(obs_mhz),
        ref_ppm=float(ref_ppm),
        nucleus=nucleus,
        meta=meta,
    )
    return fid, truth
