"""Ethanol IR walkthrough — analysis path demo (not compound ID).

Runnable twin of ``ethanol_ir_walkthrough.ipynb``. Uses the public-domain
PNNL/NIST ethanol IR JCAMP in ``fixtures/public/``.

Usage (from repo root, after ``pip install -e ".[dev,ui,baselines]"``)::

    python examples/ethanol_ir_walkthrough.py
    python examples/ethanol_ir_walkthrough.py --save-dir /tmp/ethanol_ir_demo

Honesty: ChemSpec / spectrum_core do **not** identify compounds. The fixture
filename and NIST title say “Ethanol” for provenance only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from spectrum_core import (
    apply_step,
    find_peaks,
    ingest,
    peaks_to_csv,
    save_session,
)

FIXTURE_REL = Path("fixtures") / "public" / "ethanol_ir_pnnl.jdx"
SOURCES_REL = Path("fixtures") / "public" / "SOURCES.md"
DEFAULT_PROMINENCE = 0.01


def find_repo_root(start: Path | None = None) -> Path:
    """Locate repo root by presence of the public ethanol JCAMP fixture."""
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
            if (p / FIXTURE_REL).is_file():
                return p
    raise FileNotFoundError(
        f"Could not find {FIXTURE_REL}. Run from the chemspec-workbench repo "
        "or pass an explicit --repo-root."
    )


def run(
    *,
    repo_root: Path | None = None,
    save_dir: Path | None = None,
    prominence: float = DEFAULT_PROMINENCE,
    show_plot: bool = False,
) -> dict:
    """Load ethanol IR → baseline → smooth → peaks → optional export.

    Returns a small result dict for smoke tests / notebooks.
    """
    root = find_repo_root(repo_root) if repo_root is None else Path(repo_root)
    fixture = root / FIXTURE_REL
    sources = root / SOURCES_REL
    if not fixture.is_file():
        raise FileNotFoundError(fixture)

    # --- Load public JCAMP (real measured spectrum; provenance only) ---
    raw = ingest(fixture)

    # --- Processing pipeline: baseline + light smooth ---
    working, history = apply_step(
        raw, None, "baseline", {"method": "polynomial", "degree": 2}
    )
    working, history = apply_step(
        working, history, "smooth", {"window_length": 11, "polyorder": 3}
    )

    # --- Peak pick with FWHM / area ---
    peaks = find_peaks(working, prominence=prominence)

    out: dict = {
        "fixture": str(fixture),
        "sources": str(sources) if sources.is_file() else None,
        "title": raw.title,
        "n_points": len(raw),
        "x_unit": raw.x_unit,
        "y_unit": raw.y_unit,
        "x_min": float(np.nanmin(raw.x)),
        "x_max": float(np.nanmax(raw.x)),
        "n_peaks": len(peaks),
        "prominence": prominence,
        "history_steps": [s.name for s in history.steps],
        "peaks": peaks,
        "raw": raw,
        "working": working,
        "history": history,
    }

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(raw.x, raw.y, color="0.65", lw=0.8, label="raw")
    ax.plot(working.x, working.y, color="C0", lw=1.2, label="baseline + smooth")
    if peaks:
        ax.scatter(
            [p.x for p in peaks],
            [p.y for p in peaks],
            color="C3",
            s=28,
            zorder=5,
            label=f"peaks (n={len(peaks)})",
        )
    ax.set_xlabel("Wavenumber (cm⁻¹)")
    ax.set_ylabel("Intensity (as ingested)")
    ax.set_title(
        "ChemSpec walkthrough — public ethanol IR fixture (analysis only; not ID)"
    )
    ax.invert_xaxis()  # IR convention
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save_dir is not None:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        fig_path = save_dir / "ethanol_ir_walkthrough.png"
        fig.savefig(fig_path, dpi=120)
        out["figure"] = str(fig_path)

        csv_path = save_dir / "ethanol_ir_peaks.csv"
        peaks_to_csv(peaks, csv_path)
        out["peaks_csv"] = str(csv_path)

        session_path = save_dir / "ethanol_ir_walkthrough.csw.json"
        save_session(
            session_path,
            raw,
            history=history,
            peaks=peaks,
            notes=(
                "Ethanol IR tutorial walkthrough. "
                "Session is an analysis snapshot — not compound identification. "
                f"See {SOURCES_REL.as_posix()} for license/source."
            ),
            source_path=str(fixture),
            processing={
                "baseline_on": True,
                "baseline_method": "polynomial",
                "baseline_degree": 2,
                "prominence": prominence,
            },
        )
        out["session"] = str(session_path)

    if show_plot:
        # Interactive backends only; Agg default for CI/script.
        plt.show()
    plt.close(fig)

    return out


def _print_summary(result: dict) -> None:
    print("ChemSpec — ethanol IR walkthrough (analysis path, not compound ID)")
    print(f"  fixture : {result['fixture']}")
    if result.get("sources"):
        print(f"  source  : {result['sources']}  (NIST/PNNL; Owner: Public domain)")
    print(f"  title   : {result['title']}  (NIST label — provenance only)")
    print(f"  points  : {result['n_points']}")
    print(f"  x_unit  : {result['x_unit']}   y_unit: {result['y_unit']}")
    print(f"  x range : {result['x_min']:.1f} … {result['x_max']:.1f}")
    print(f"  pipeline: {' → '.join(result['history_steps'])}")
    print(f"  peaks   : {result['n_peaks']}  (prominence={result['prominence']})")
    print()
    print(
        f"{'idx':>6}  {'x':>10}  {'y':>12}  {'prominence':>12}  "
        f"{'FWHM':>12}  {'area':>12}"
    )
    print("-" * 72)
    for p in result["peaks"][:15]:
        fwhm_s = f"{p.fwhm:12.4f}" if p.fwhm == p.fwhm else f"{'nan':>12}"
        area_s = f"{p.area:12.4f}" if p.area == p.area else f"{'nan':>12}"
        print(
            f"{p.index:6d}  {p.x:10.1f}  {p.y:12.6g}  {p.prominence:12.6g}  "
            f"{fwhm_s}  {area_s}"
        )
    if result["n_peaks"] > 15:
        print(f"  … {result['n_peaks'] - 15} more")
    print()
    if result.get("peaks_csv"):
        print(f"  peaks CSV : {result['peaks_csv']}")
    if result.get("session"):
        print(f"  session   : {result['session']}")
    if result.get("figure"):
        print(f"  figure    : {result['figure']}")
    print()
    print(
        "Disclaimer: no compound identification. Peak x/y/FWHM/area are "
        "geometric metrics on the loaded trace only."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ethanol IR analysis walkthrough (not compound ID)"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="chemspec-workbench repo root (auto-detected if omitted)",
    )
    parser.add_argument(
        "--save-dir",
        type=Path,
        default=None,
        help="optional directory for PNG, peaks CSV, and .csw.json session",
    )
    parser.add_argument(
        "--prominence",
        type=float,
        default=DEFAULT_PROMINENCE,
        help=f"peak prominence (default {DEFAULT_PROMINENCE})",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="call plt.show() (needs an interactive matplotlib backend)",
    )
    args = parser.parse_args(argv)
    result = run(
        repo_root=args.repo_root,
        save_dir=args.save_dir,
        prominence=args.prominence,
        show_plot=args.show,
    )
    _print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
