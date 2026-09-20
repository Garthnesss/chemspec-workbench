"""Acetone UV-Vis walkthrough — analysis path demo (not compound ID).

Runnable twin of ``acetone_uvvis_walkthrough.ipynb``. Uses the NIST Chemistry
WebBook acetone UV-Vis JCAMP in ``fixtures/public/``.

Usage (from repo root, after ``pip install -e ".[dev,ui,baselines]"``)::

    python examples/acetone_uvvis_walkthrough.py
    python examples/acetone_uvvis_walkthrough.py --save-dir /tmp/acetone_uvvis_demo

Honesty: ChemSpec / spectrum_core do **not** identify compounds. The fixture
filename and NIST title say “Acetone” for provenance only.

Y-axis note: JCAMP ``##YUNITS=Logarithm epsilon`` is log₁₀(ε) (molar
absorptivity). Ingest stores ``y_unit=intensity`` — **not** absorbance (A).
Do **not** run A ↔ %T conversion on this trace without first converting from ε
(needs path length and concentration — out of scope here).
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

FIXTURE_REL = Path("fixtures") / "public" / "acetone_uvvis_nist.jdx"
SOURCES_REL = Path("fixtures") / "public" / "SOURCES.md"
DEFAULT_PROMINENCE = 0.05  # broad band after poly baseline (benzene twin uses 0.1)


def find_repo_root(start: Path | None = None) -> Path:
    """Locate repo root by presence of the public acetone UV-Vis JCAMP fixture."""
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
    """Load acetone UV-Vis → baseline → smooth → peaks → optional export.

    Returns a small result dict for smoke tests / notebooks.
    """
    root = find_repo_root(repo_root) if repo_root is None else Path(repo_root)
    fixture = root / FIXTURE_REL
    sources = root / SOURCES_REL
    if not fixture.is_file():
        raise FileNotFoundError(fixture)

    # --- Load public JCAMP (real measured spectrum; provenance only) ---
    raw = ingest(fixture)
    unit_notes = list(raw.meta.get("unit_notes") or [])
    jcamp_yunits = raw.meta.get("jcamp_yunits")

    # --- Processing pipeline: light baseline + smooth (sensible on log ε) ---
    working, history = apply_step(
        raw, None, "baseline", {"method": "polynomial", "degree": 2}
    )
    working, history = apply_step(
        working, history, "smooth", {"window_length": 7, "polyorder": 2}
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
        "jcamp_yunits": jcamp_yunits,
        "unit_notes": unit_notes,
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

    # --- Plot (wavelength ascending; y is log₁₀(ε) intensity, not A) ---
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
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("log₁₀(ε) intensity (as ingested — not absorbance)")
    ax.set_title(
        "ChemSpec walkthrough — public acetone UV-Vis fixture "
        "(analysis only; not ID)"
    )
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save_dir is not None:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        fig_path = save_dir / "acetone_uvvis_walkthrough.png"
        fig.savefig(fig_path, dpi=120)
        out["figure"] = str(fig_path)

        csv_path = save_dir / "acetone_uvvis_peaks.csv"
        peaks_to_csv(peaks, csv_path)
        out["peaks_csv"] = str(csv_path)

        session_path = save_dir / "acetone_uvvis_walkthrough.csw.json"
        save_session(
            session_path,
            raw,
            history=history,
            peaks=peaks,
            notes=(
                "Acetone UV-Vis tutorial walkthrough. "
                "Session is an analysis snapshot — not compound identification. "
                "Y is log10(epsilon) intensity, not absorbance; do not run "
                f"A↔%T without converting from ε. See {SOURCES_REL.as_posix()}."
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
    print(
        "ChemSpec — acetone UV-Vis walkthrough "
        "(analysis path, not compound ID)"
    )
    print(f"  fixture : {result['fixture']}")
    if result.get("sources"):
        print(
            f"  source  : {result['sources']}  "
            "(NIST WebBook SRD 69; OWNER=INEP CP RAS, NIST OSRD — see SOURCES.md)"
        )
    print(f"  title   : {result['title']}  (NIST label — provenance only)")
    print(f"  points  : {result['n_points']}")
    print(f"  x_unit  : {result['x_unit']}   y_unit: {result['y_unit']}")
    if result.get("jcamp_yunits"):
        print(
            f"  JCAMP YUNITS: {result['jcamp_yunits']}  "
            "→ stored as intensity (log₁₀(ε)), NOT absorbance"
        )
    for note in result.get("unit_notes") or []:
        print(f"  unit_notes: {note}")
    print(f"  x range : {result['x_min']:.1f} … {result['x_max']:.1f} nm")
    print(f"  pipeline: {' → '.join(result['history_steps'])}")
    print(f"  peaks   : {result['n_peaks']}  (prominence={result['prominence']})")
    print()
    print(
        "  Note: do not run A ↔ %T on this trace without converting from ε "
        "(path length + concentration required)."
    )
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
        description="Acetone UV-Vis analysis walkthrough (not compound ID)"
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
