"""FID/NMR walkthrough — synthetic mock FID → FFT/phase → peaks (not compound ID).

Thin educational twin of the ``fidnmr-demo`` CLI path. No licensed FID fixtures
yet; uses ``fidnmr.generate_mock_fid`` only. Notebook twin deferred (script +
pytest smoke is enough for Phase-0).

Usage (from repo root, after ``pip install -e ".[dev]"``)::

    python examples/fidnmr_walkthrough.py
    python examples/fidnmr_walkthrough.py --save-dir /tmp/fidnmr_demo

Honesty: synthetic educational stub — **not** a real acquisition, **not**
structure elucidation / compound ID. No magnet or vendor FID files required.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from spectrum_core import find_peaks, peaks_to_csv
from spectrum_core.spectrum import Spectrum

from fidnmr import apodize_exp, fid_to_spectrum, generate_mock_fid
from fidnmr.mock_source import DEFAULT_TEACHING_PEAKS_PPM

DEFAULT_PROMINENCE_FRAC = 0.05


def find_repo_root(start: Path | None = None) -> Path:
    """Locate repo root by presence of the ``fidnmr`` package."""
    candidates: list[Path] = []
    if start is not None:
        candidates.append(start.resolve())
    candidates.append(Path.cwd().resolve())
    here = Path(__file__).resolve().parent
    candidates.extend([here, here.parent])
    seen: set[Path] = set()
    for base in candidates:
        for p in [base, *base.parents]:
            if p in seen:
                continue
            seen.add(p)
            if (p / "fidnmr" / "__init__.py").is_file() and (
                p / "spectrum_core" / "__init__.py"
            ).is_file():
                return p
    raise FileNotFoundError(
        "Could not find chemspec-workbench repo root (fidnmr/ + spectrum_core/). "
        "Run from the repo or pass --repo-root."
    )


def run(
    *,
    repo_root: Path | None = None,
    save_dir: Path | None = None,
    npts: int = 2048,
    lb_hz: float = 1.0,
    phc0_deg: float = 0.0,
    prominence: float | None = None,
    show_plot: bool = False,
) -> dict:
    """Mock FID → apodize → FFT/phase → peaks → optional plot/CSV.

    Returns a small result dict for smoke tests.
    """
    root = find_repo_root(repo_root) if repo_root is None else Path(repo_root)
    # Ensure imports resolve when invoked as a script path
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    fid, truth = generate_mock_fid(
        npts=npts,
        peaks_ppm=DEFAULT_TEACHING_PEAKS_PPM,
        noise_std=0.0,
        seed=42,
    )
    # Apodize is also applied inside fid_to_spectrum; expose a copy for the
    # time-domain plot so the walkthrough shows the educational FID→FFT path.
    fid_lb = apodize_exp(fid, lb_hz=lb_hz) if lb_hz else fid
    spec = fid_to_spectrum(
        fid,
        lb_hz=lb_hz,
        phc0_deg=phc0_deg,
        x_unit="ppm",
        title=str(fid.meta.get("title", "FID/NMR mock")),
    )

    pick = Spectrum(
        x=spec.x,
        y=np.abs(spec.y),
        x_unit=spec.x_unit,
        y_unit=spec.y_unit,
        title=spec.title,
        meta=dict(spec.meta),
    )
    if prominence is None:
        prominence = float(np.max(np.abs(spec.y))) * DEFAULT_PROMINENCE_FRAC
    peaks = find_peaks(pick, prominence=prominence)
    peaks = sorted(peaks, key=lambda p: p.y, reverse=True)

    out: dict = {
        "repo_root": str(root),
        "synthetic": True,
        "title": spec.title,
        "n_points": len(spec),
        "x_unit": spec.x_unit,
        "y_unit": spec.y_unit,
        "npts_fid": npts,
        "lb_hz": lb_hz,
        "phc0_deg": phc0_deg,
        "expected_peaks_ppm": list(truth["peaks_ppm"]),
        "n_peaks": len(peaks),
        "prominence": prominence,
        "peaks": peaks,
        "fid": fid,
        "spectrum": spec,
    }

    # --- Plot: |FID| time + spectrum (ppm) ---
    t = np.arange(fid_lb.signal.size, dtype=float) / float(fid.sw_hz)
    fig, axes = plt.subplots(2, 1, figsize=(8, 6), constrained_layout=True)
    axes[0].plot(t * 1e3, np.abs(fid_lb.signal), color="C0", lw=0.8)
    axes[0].set_xlabel("time (ms)")
    axes[0].set_ylabel("|FID| (a.u.)")
    axes[0].set_title("Synthetic FID (apodized) — not a real acquisition")
    axes[1].plot(spec.x, np.real(spec.y), color="C1", lw=0.9, label="Re")
    axes[1].plot(spec.x, np.abs(spec.y), color="C2", lw=0.7, alpha=0.7, label="|y|")
    for p in peaks[:12]:
        axes[1].axvline(p.x, color="0.5", ls=":", lw=0.6)
    axes[1].invert_xaxis()  # conventional NMR: high ppm left
    axes[1].set_xlabel("ppm (teaching axis)")
    axes[1].set_ylabel("intensity")
    axes[1].set_title(f"{spec.title} — mock FFT/phase (no compound ID)")
    axes[1].legend(loc="upper right", fontsize=8)
    fig.suptitle(
        "FID/NMR walkthrough — synthetic educational stub (no magnet)",
        fontsize=11,
    )

    if save_dir is not None:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        fig_path = save_dir / "fidnmr_walkthrough.png"
        csv_path = save_dir / "fidnmr_peaks.csv"
        fig.savefig(fig_path, dpi=120)
        peaks_to_csv(peaks, csv_path)
        out["figure"] = str(fig_path)
        out["peaks_csv"] = str(csv_path)

    if show_plot:
        plt.show()
    else:
        plt.close(fig)

    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="FID/NMR Phase-0 walkthrough (synthetic mock; no magnet)."
    )
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--save-dir", type=Path, default=None)
    parser.add_argument("--npts", type=int, default=2048)
    parser.add_argument("--lb-hz", type=float, default=1.0)
    parser.add_argument("--phc0", type=float, default=0.0, dest="phc0_deg")
    parser.add_argument(
        "--prominence",
        type=float,
        default=None,
        help="Peak prominence on |y|; default = 5%% of max |y|",
    )
    parser.add_argument("--show", action="store_true", help="Show matplotlib window")
    args = parser.parse_args(argv)

    result = run(
        repo_root=args.repo_root,
        save_dir=args.save_dir,
        npts=args.npts,
        lb_hz=args.lb_hz,
        phc0_deg=args.phc0_deg,
        prominence=args.prominence,
        show_plot=args.show,
    )

    print("FID/NMR walkthrough — synthetic 1H-like mock (not a real acquisition)")
    print(f"  npts   : {result['npts_fid']}; x_unit={result['x_unit']}")
    print(f"  lb_hz  : {result['lb_hz']}; phc0={result['phc0_deg']}°")
    print(
        "  expected teaching ppm:",
        ", ".join(f"{x:.1f}" for x in result["expected_peaks_ppm"]),
    )
    print(f"  peaks  : {result['n_peaks']} (prominence={result['prominence']:.4g} on |y|)")
    print()
    print(f"{'ppm':>10}  {'|y|':>10}  {'prominence':>10}")
    for p in result["peaks"][:16]:
        print(f"{p.x:10.3f}  {p.y:10.4f}  {p.prominence:10.4f}")
    if result.get("figure"):
        print()
        print(f"  wrote figure : {result['figure']}")
        print(f"  wrote peaks  : {result['peaks_csv']}")
    print()
    print(
        "Disclaimer: synthetic educational stub — not hardware-verified; "
        "not compound ID / structure elucidation."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
