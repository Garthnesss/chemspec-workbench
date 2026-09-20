"""Synthetic line-spectrum frames for TeachSpec demos and tests.

No camera libraries. Peaks resemble a teaching CFL-like pattern (approximate
visible mercury / phosphor teaching lines) but are **labeled synthetic** —
not a real capture and not compound identification.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from teachspec.optical import OpticalLiveFrame

# Approximate visible teaching lines (nm) used only for mock generation.
# Not a claim that a real CFL was measured.
DEFAULT_CFL_LIKE_LINES_NM: tuple[float, ...] = (
    405.0,
    436.0,
    546.0,
    577.0,
    611.0,
)


def generate_mock_frame(
    n_pixels: int = 640,
    *,
    wavelength_range_nm: tuple[float, float] = (380.0, 700.0),
    lines_nm: Sequence[float] | None = None,
    line_amps: Sequence[float] | None = None,
    sigma_pixels: float = 2.5,
    noise_std: float = 0.02,
    baseline: float = 0.05,
    seed: int | None = 42,
) -> tuple[OpticalLiveFrame, dict]:
    """Generate a synthetic 1-D intensity frame with Gaussian line peaks.

    Internally places lines on a linear pixel↔nm map spanning
    ``wavelength_range_nm`` so tests can recover peaks after fitting that
    same map. Returns ``(frame, truth_meta)`` where ``truth_meta`` includes
    the generating linear coefficients (for tests only).

    This is **synthetic** teaching data — not a live camera capture.
    """
    if n_pixels < 8:
        raise ValueError("n_pixels must be >= 8")
    wl0, wl1 = float(wavelength_range_nm[0]), float(wavelength_range_nm[1])
    if wl1 <= wl0:
        raise ValueError("wavelength_range_nm must be increasing")

    lines = list(DEFAULT_CFL_LIKE_LINES_NM if lines_nm is None else lines_nm)
    if not lines:
        raise ValueError("lines_nm must be non-empty")
    if line_amps is None:
        amps = [1.0] * len(lines)
    else:
        amps = [float(a) for a in line_amps]
        if len(amps) != len(lines):
            raise ValueError("line_amps length must match lines_nm")

    # Linear map: nm = a*pixel + b  (pixel 0 → wl0, pixel n-1 → wl1)
    a = (wl1 - wl0) / float(n_pixels - 1)
    b = wl0
    pixels = np.arange(n_pixels, dtype=float)
    intensity = np.full(n_pixels, float(baseline), dtype=float)

    for wl, amp in zip(lines, amps):
        # pixel = (nm - b) / a
        center_px = (float(wl) - b) / a
        intensity += amp * np.exp(
            -0.5 * ((pixels - center_px) / float(sigma_pixels)) ** 2
        )

    if noise_std > 0:
        rng = np.random.default_rng(seed)
        intensity = intensity + rng.normal(0.0, float(noise_std), n_pixels)

    meta = {
        "synthetic": True,
        "source": "teachspec.mock_source.generate_mock_frame",
        "title": "Synthetic CFL-like TeachSpec frame (not a real capture)",
        "n_pixels": int(n_pixels),
        "wavelength_range_nm": [wl0, wl1],
        "lines_nm": [float(x) for x in lines],
        "line_amps": amps,
        "sigma_pixels": float(sigma_pixels),
        "noise_std": float(noise_std),
        "baseline": float(baseline),
        "seed": seed,
        "disclaimer": (
            "Synthetic educational mock — not hardware-verified; "
            "not compound identification."
        ),
    }
    truth = {
        "linear_coefficients": [a, b],  # highest degree first
        "wavelength_range_nm": [wl0, wl1],
        "lines_nm": [float(x) for x in lines],
    }
    return OpticalLiveFrame(intensity=intensity, meta=meta), truth
