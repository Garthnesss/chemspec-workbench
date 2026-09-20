"""FID → FFT → phase → spectrum_core.Spectrum (educational stub).

No structure elucidation / compound ID. Wavelength/shift axes are teaching
helpers from declared ``obs_mhz`` + ``ref_ppm``, not metrology claims.
"""

from __future__ import annotations

from typing import Literal

import numpy as np

from spectrum_core.spectrum import Spectrum, XUnit
from fidnmr.fid import FID

AxisUnit = Literal["Hz", "ppm"]


def apodize_exp(fid: FID, *, lb_hz: float = 0.0) -> FID:
    """Exponential line broadening: multiply FID by ``exp(-π · lb_hz · t)``.

    ``lb_hz`` is the Lorentzian line-broadening parameter in Hz (0 = no-op).
    Returns a new ``FID`` (does not mutate the input).
    """
    lb = float(lb_hz)
    if lb < 0:
        raise ValueError("lb_hz must be >= 0")
    if lb == 0.0:
        return FID(
            signal=fid.signal.copy(),
            sw_hz=fid.sw_hz,
            obs_mhz=fid.obs_mhz,
            ref_ppm=fid.ref_ppm,
            nucleus=fid.nucleus,
            meta={**dict(fid.meta), "apodization": {"kind": "none"}},
        )
    t = fid.time_axis_s()
    window = np.exp(-np.pi * lb * t)
    meta = {
        **dict(fid.meta),
        "apodization": {"kind": "exp", "lb_hz": lb},
    }
    return FID(
        signal=fid.signal * window,
        sw_hz=fid.sw_hz,
        obs_mhz=fid.obs_mhz,
        ref_ppm=fid.ref_ppm,
        nucleus=fid.nucleus,
        meta=meta,
    )


def apply_phase(
    spectrum_complex: np.ndarray,
    freqs_hz: np.ndarray,
    *,
    phc0_deg: float = 0.0,
    phc1_deg: float = 0.0,
) -> np.ndarray:
    """Zero- and first-order phase correction on a complex frequency spectrum.

    ``phc0_deg`` is a global phase (degrees). ``phc1_deg`` is the additional
    phase at the positive edge of the spectral width (degrees), applied
    linearly across ``freqs_hz`` normalized to ±0.5 · span.
    """
    z = np.asarray(spectrum_complex)
    f = np.asarray(freqs_hz, dtype=float)
    if z.shape != f.shape:
        raise ValueError("spectrum_complex and freqs_hz shape mismatch")
    span = float(np.ptp(f))
    if span <= 0:
        raise ValueError("freqs_hz must span a positive range")
    # Normalize frequency to [-0.5, 0.5] relative to center
    f0 = 0.5 * (float(f[0]) + float(f[-1]))
    f_norm = (f - f0) / span
    phase_rad = np.deg2rad(float(phc0_deg) + float(phc1_deg) * f_norm)
    return z * np.exp(-1j * phase_rad)


def hz_to_ppm(freqs_hz: np.ndarray, *, obs_mhz: float, ref_ppm: float = 0.0) -> np.ndarray:
    """Convert carrier-relative Hz offsets to ppm.

    ``ppm = ref_ppm + f_hz / obs_mhz`` (obs in MHz, f in Hz → ppm).
    Teaching convention for this stub — document in meta; not a claim of
    vendor-calibrated referencing.
    """
    if float(obs_mhz) <= 0:
        raise ValueError("obs_mhz must be positive")
    return float(ref_ppm) + np.asarray(freqs_hz, dtype=float) / float(obs_mhz)


def fid_to_spectrum(
    fid: FID,
    *,
    lb_hz: float = 0.0,
    phc0_deg: float = 0.0,
    phc1_deg: float = 0.0,
    x_unit: AxisUnit = "ppm",
    title: str = "",
    real_only: bool = True,
) -> Spectrum:
    """FFT a FID, apply phase, return a real (or magnitude) ``Spectrum``.

    Default ``x_unit='ppm'`` uses ``obs_mhz`` + ``ref_ppm``. Set ``x_unit='Hz'``
    for the carrier-relative frequency axis. Educational only — not compound ID.
    """
    if x_unit not in ("Hz", "ppm"):
        raise ValueError("x_unit must be 'Hz' or 'ppm'")

    worked = apodize_exp(fid, lb_hz=lb_hz) if lb_hz else fid
    n = worked.npts
    # fftshift so DC/carrier is center; freqs from -sw/2 .. +sw/2
    spectrum_c = np.fft.fftshift(np.fft.fft(worked.signal, n=n))
    freqs_hz = np.fft.fftshift(np.fft.fftfreq(n, d=worked.dwell_s))
    spectrum_c = apply_phase(
        spectrum_c, freqs_hz, phc0_deg=phc0_deg, phc1_deg=phc1_deg
    )

    if real_only:
        y = np.real(spectrum_c).astype(float)
        y_mode = "real"
    else:
        y = np.abs(spectrum_c).astype(float)
        y_mode = "magnitude"

    if x_unit == "ppm":
        x = hz_to_ppm(freqs_hz, obs_mhz=worked.obs_mhz, ref_ppm=worked.ref_ppm)
        xu: XUnit = "ppm"
    else:
        x = freqs_hz.astype(float)
        xu = "Hz"

    meta = {
        **dict(worked.meta),
        "fidnmr": {
            "sw_hz": worked.sw_hz,
            "obs_mhz": worked.obs_mhz,
            "ref_ppm": worked.ref_ppm,
            "nucleus": worked.nucleus,
            "npts": n,
            "lb_hz": float(lb_hz),
            "phc0_deg": float(phc0_deg),
            "phc1_deg": float(phc1_deg),
            "y_mode": y_mode,
            "freqs_hz_span": [float(freqs_hz[0]), float(freqs_hz[-1])],
        },
        "source": worked.meta.get("source", "fidnmr.process.fid_to_spectrum"),
        "disclaimer": (
            "Educational FID→FFT stub — not a live spectrometer; "
            "not compound identification / structure elucidation."
        ),
    }
    return Spectrum(
        x=x,
        y=y,
        x_unit=xu,
        y_unit="intensity",
        title=title
        or str(worked.meta.get("title", f"FID/NMR {worked.nucleus} spectrum")),
        meta=meta,
    )
