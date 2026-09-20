"""CLI demo: TeachSpec mock (default) or optional live OpenCV UVC.

Usage:
    python -m teachspec.demo
    python -m teachspec
    teachspec-demo
    teachspec-demo --live --device 0   # requires: pip install -e ".[teachspec]"

Educational only — no compound ID. Default is ``--mock`` (camera-free).
Live UVC is intensity vs pixel until calibrated via teachspec.calibration.
Classroom use remains subject to docs/family/teachspec/SAFETY.md.
"""

from __future__ import annotations

import argparse

from spectrum_core import find_peaks

from teachspec.calibration import fit_wavelength_calibration
from teachspec.mock_source import DEFAULT_CFL_LIKE_LINES_NM, generate_mock_frame
from teachspec.optical import OpticalLiveFrame, frame_to_spectrum


def _run_mock(*, n_pixels: int = 640, prominence: float = 0.15) -> int:
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


def _run_live(*, device: int, row: int | None, prominence: float) -> int:
    from teachspec.uvc_ingest import open_uvc_source

    with open_uvc_source(device_index=device, row=row) as src:
        frame: OpticalLiveFrame = src.read_frame()

    print("TeachSpec demo — live UVC OpenCV capture (intensity vs pixel)")
    print(f"  device : {device}")
    print(f"  source : {frame.meta.get('source')}")
    print(f"  pixels : {frame.intensity.size}")
    print(f"  row    : {frame.meta.get('row')}")
    print(f"  calibrated: {frame.meta.get('wavelength_calibrated')}")
    print()
    print(
        "Honesty: camera path is intensity vs pixel until you apply "
        "teachspec.calibration (pixel→nm). Not compound ID; not "
        "hardware-verified wavelength by camera alone."
    )
    print("Safety: live classroom use is subject to docs/family/teachspec/SAFETY.md.")
    # Optional peak pick on pixel index as teaching preview (not nm).
    # Build a trivial identity calibration so Spectrum x is pixel index labeled nm-less.
    # Prefer raw intensity summary without fake nm: print stats only.
    print()
    print(f"  intensity min/max: {float(frame.intensity.min()):.4g} / {float(frame.intensity.max()):.4g}")
    print(f"  prominence preview skipped without wavelength calibration (prominence={prominence})")
    if frame.meta.get("disclaimer"):
        print()
        print(frame.meta["disclaimer"])
    return 0


def run(*, n_pixels: int = 640, prominence: float = 0.15) -> int:
    """Backward-compatible entry: mock path only."""
    return _run_mock(n_pixels=n_pixels, prominence=prominence)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "TeachSpec demo — default mock (camera-free); "
            "optional --live OpenCV UVC (requires [teachspec] extra)."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--mock",
        action="store_true",
        help="Synthetic CFL-like mock (default; camera-free)",
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help="Live UVC via OpenCV (requires: pip install -e \".[teachspec]\")",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=0,
        help="UVC device index for --live (default: 0)",
    )
    parser.add_argument(
        "--row",
        type=int,
        default=None,
        help="Row index to extract for --live (default: image mid-line)",
    )
    parser.add_argument("--n-pixels", type=int, default=640, help="Mock frame width")
    parser.add_argument("--prominence", type=float, default=0.15)
    args = parser.parse_args(argv)

    if args.live:
        return _run_live(device=args.device, row=args.row, prominence=args.prominence)
    return _run_mock(n_pixels=args.n_pixels, prominence=args.prominence)


if __name__ == "__main__":
    raise SystemExit(main())
