"""CLI demo: mock FID → FFT/phase → Spectrum → peak table.

Usage:
    python -m fidnmr.demo
    python -m fidnmr
    fidnmr-demo

Educational / synthetic only — no magnet, no compound ID.
"""

from __future__ import annotations

import argparse

import numpy as np

from spectrum_core import find_peaks
from spectrum_core.spectrum import Spectrum

from fidnmr.mock_source import DEFAULT_TEACHING_PEAKS_PPM, generate_mock_fid
from fidnmr.process import fid_to_spectrum


def run(
    *,
    npts: int = 2048,
    lb_hz: float = 1.0,
    phc0_deg: float = 0.0,
    prominence: float | None = None,
) -> int:
    fid, _truth = generate_mock_fid(npts=npts, seed=42)
    spec = fid_to_spectrum(
        fid,
        lb_hz=lb_hz,
        phc0_deg=phc0_deg,
        x_unit="ppm",
        title=str(fid.meta.get("title", "")),
    )
    # Peak pick on |y| so phase sign does not hide absorption lines
    pick = Spectrum(
        x=spec.x,
        y=np.abs(spec.y),
        x_unit=spec.x_unit,
        y_unit=spec.y_unit,
        title=spec.title,
        meta=dict(spec.meta),
    )
    if prominence is None:
        prominence = float(np.max(np.abs(spec.y))) * 0.05
    peaks = find_peaks(pick, prominence=prominence)
    peaks = sorted(peaks, key=lambda p: p.y, reverse=True)

    print("FID/NMR demo — synthetic 1H-like mock (not a real acquisition)")
    print(f"  npts   : {npts}; sw={fid.sw_hz:g} Hz; obs={fid.obs_mhz:g} MHz")
    print(f"  lb_hz  : {lb_hz}; phc0={phc0_deg}°")
    print(f"  x_unit : {spec.x_unit}; y_unit: {spec.y_unit}")
    print(f"  peaks  : {len(peaks)} (prominence={prominence:.4g} on |y|)")
    print(
        "  expected teaching ppm:",
        ", ".join(f"{x:.1f}" for x in DEFAULT_TEACHING_PEAKS_PPM),
    )
    print()
    print(f"{'ppm':>10}  {'|y|':>10}  {'prominence':>10}")
    for p in peaks[:16]:
        print(f"{p.x:10.3f}  {p.y:10.4f}  {p.prominence:10.4f}")
    print()
    print(
        "Disclaimer: synthetic educational stub — not hardware-verified; "
        "not compound ID / structure elucidation."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="FID/NMR Phase-0 mock demo (synthetic peaks, no magnet)."
    )
    parser.add_argument("--npts", type=int, default=2048)
    parser.add_argument("--lb-hz", type=float, default=1.0)
    parser.add_argument("--phc0", type=float, default=0.0, dest="phc0_deg")
    parser.add_argument("--prominence", type=float, default=None,
                        help="Peak prominence on |y|; default = 5% of max |y|")
    args = parser.parse_args(argv)
    return run(
        npts=args.npts,
        lb_hz=args.lb_hz,
        phc0_deg=args.phc0_deg,
        prominence=args.prominence,
    )


if __name__ == "__main__":
    raise SystemExit(main())
