"""IQ → power spectrum (FFT + window) as spectrum_core.Spectrum."""

from __future__ import annotations

from typing import Literal

import numpy as np
from scipy.signal import get_window

from spectrum_core.spectrum import Spectrum, XUnit, YUnit

WindowName = Literal["hann", "hamming", "blackman", "boxcar", "flattop"]


def iq_to_spectrum(
    iq: np.ndarray,
    *,
    sample_rate: float,
    center_freq: float = 0.0,
    window: WindowName | str = "hann",
    x_unit: XUnit = "MHz",
    y_unit: YUnit = "dB",
    title: str = "",
    meta: dict | None = None,
) -> Spectrum:
    """Convert complex IQ to a power spectrum ``Spectrum``.

    Parameters
    ----------
    iq :
        Complex baseband samples.
    sample_rate :
        Sample rate in Hz (span ≈ sample_rate).
    center_freq :
        RF center frequency in Hz (added to baseband FFT bins).
    window :
        SciPy window name applied before FFT.
    x_unit :
        ``"Hz"`` or ``"MHz"`` (RF absolute frequency axis).
    y_unit :
        ``"dB"`` (10·log10 power) or ``"intensity"`` (linear power).
    """
    iq = np.asarray(iq)
    if iq.ndim != 1:
        raise ValueError("iq must be 1-D")
    if len(iq) < 8:
        raise ValueError("iq length must be >= 8")
    if not np.iscomplexobj(iq):
        raise ValueError("iq must be complex")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    if x_unit not in ("Hz", "MHz"):
        raise ValueError(f"RF spectrum x_unit must be 'Hz' or 'MHz', got {x_unit!r}")
    if y_unit not in ("dB", "intensity"):
        raise ValueError(f"RF spectrum y_unit must be 'dB' or 'intensity', got {y_unit!r}")

    n = len(iq)
    win = get_window(window, n, fftbins=True).astype(float)
    # Coherent gain normalize so windowing does not scale power arbitrarily
    win = win / (np.sum(win) / n)
    windowed = iq * win
    spectrum = np.fft.fftshift(np.fft.fft(windowed, n=n))
    power = (np.abs(spectrum) ** 2) / n
    freqs_bb = np.fft.fftshift(np.fft.fftfreq(n, d=1.0 / sample_rate))
    freqs_hz = freqs_bb + float(center_freq)

    if x_unit == "MHz":
        x = freqs_hz / 1e6
    else:
        x = freqs_hz

    if y_unit == "dB":
        # Floor to avoid -inf
        y = 10.0 * np.log10(np.maximum(power, 1e-20))
    else:
        y = power

    out_meta = {
        "sample_rate": float(sample_rate),
        "center_freq": float(center_freq),
        "window": str(window),
        "n_fft": int(n),
        "domain": "rf_power_spectrum",
        **(meta or {}),
    }
    return Spectrum(
        x=x,
        y=y,
        x_unit=x_unit,
        y_unit=y_unit,
        title=title or "RF power spectrum",
        meta=out_meta,
    )
