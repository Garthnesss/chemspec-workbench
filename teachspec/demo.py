"""CLI demo: mock TeachSpec frame → calibrated Spectrum → peak table.

Usage:
    python -m teachspec.demo
    python -m teachspec

Educational / synthetic only — no camera, no compound ID.
"""

from __future__ import annotations

import argparse

from spectrum_core import find_peaks

from teachspec.calibration import fit_wavelength_calibration
from teachspec.mock_source import DEFAULT_CFL_LIKE_LINES_NM, generate_mock_frame
from teachspec.optical import frame_to_spectrum


def run(*, n_pixels: int = 640, prominence: float = 0.15) -> int:
    frame, truth = generate_mock_frame(n_pixels=n_pixels, seed=42)
    # Fit from the known generating lines placed at their true pixels.
    a, b = truth["linear_coefficients"]
    lines = truth["lines_nm"]
    pixels = [(wl - b) / a for wl in lines]
    cal = fit_wavelength_calibration(pixels, lines, fit_kind="linear")
    spec = frame_to_spectrum(frame, cal, title=frame.meta.get("title", ""))
    peaks = find_peaks(spec, prominence=prominence)

    print("TeachSpec demo — synthetic CFL-like mock (not a real capture)")
    print(f"  pixels : {n_pixels}")
    print(f"  fit    : {cal.fit_kind}; RMSE≈{cal.rmse_nm:.4g} nm (fit points)")
    print(f"  x_unit : {spec.x_unit}; y_unit: {spec.y_unit}")
    print(f"  peaks  : {len(peaks)} (prominence={prominence})")
    print("  expected teaching lines (nm):", ", ".join(f"{x:.0f}" for x in DEFAULT_CFL_LIKE_LINES_NM))
    print()
    print(f"{'x_nm':>10}  {'intensity':>10}  {'prominence':>10}")
    for p in peaks[:12]:
        print(f"{p.x:10.2f}  {p.y:10.4f}  {p.prominence:10.4f}")
    print()
    print("Disclaimer: synthetic educational stub — not hardware-verified; not compound ID.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="TeachSpec Phase-0 mock demo (synthetic peaks, no camera)."
    )
    parser.add_argument("--n-pixels", type=int, default=640)
    parser.add_argument("--prominence", type=float, default=0.15)
    args = parser.parse_args(argv)
    return run(n_pixels=args.n_pixels, prominence=args.prominence)


if __name__ == "__main__":
    raise SystemExit(main())
