"""CLI demo: load a fixture, print peak table, optional baseline note.

Usage:
    python -m chemspec.demo
    python -m chemspec.demo --fixture ir
    chemspec-demo --fixture uvvis
"""

from __future__ import annotations

import argparse
from pathlib import Path

from spectrum_core import (
    baseline_polynomial,
    find_peaks,
    ingest_csv,
)

_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES = _ROOT / "fixtures"

_FIXTURE_MAP = {
    "uvvis": {
        "path": _FIXTURES / "uvvis_synthetic.csv",
        "x_col": "wavelength_nm",
        "y_col": "absorbance",
        "x_unit": "nm",
        "y_unit": "A",
        "prominence": 0.15,
    },
    "ir": {
        "path": _FIXTURES / "ir_synthetic.csv",
        "x_col": "wavenumber_cm-1",
        "y_col": "intensity",
        "x_unit": "cm-1",
        "y_unit": "intensity",
        "prominence": 0.15,
    },
}


def run(fixture: str = "uvvis", *, apply_baseline: bool = True) -> int:
    if fixture not in _FIXTURE_MAP:
        raise SystemExit(f"unknown fixture {fixture!r}; choose from {list(_FIXTURE_MAP)}")

    cfg = _FIXTURE_MAP[fixture]
    spec = ingest_csv(
        cfg["path"],
        x_col=cfg["x_col"],
        y_col=cfg["y_col"],
        x_unit=cfg["x_unit"],
        y_unit=cfg["y_unit"],
    )
    work = baseline_polynomial(spec, degree=1) if apply_baseline else spec
    peaks = find_peaks(work, prominence=cfg["prominence"])

    print(f"ChemSpec demo — fixture={fixture}")
    print(f"  file   : {cfg['path'].name}")
    print(f"  title  : {spec.title}")
    print(f"  points : {len(spec)}")
    print(f"  x_unit : {spec.x_unit}   y_unit: {spec.y_unit}")
    print(f"  baseline: {'poly degree=1' if apply_baseline else 'none'}")
    print()
    print(f"{'idx':>6}  {'x':>12}  {'y':>12}  {'prominence':>12}")
    print("-" * 50)
    for p in peaks[:20]:
        print(f"{p.index:6d}  {p.x:12.3f}  {p.y:12.4f}  {p.prominence:12.4f}")
    print()
    print("Note: synthetic fixture — no compound identification.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ChemSpec peak-table demo")
    parser.add_argument(
        "--fixture",
        choices=sorted(_FIXTURE_MAP),
        default="uvvis",
        help="which synthetic fixture to load",
    )
    parser.add_argument(
        "--no-baseline",
        action="store_true",
        help="skip polynomial baseline before peak pick",
    )
    args = parser.parse_args(argv)
    return run(args.fixture, apply_baseline=not args.no_baseline)


if __name__ == "__main__":
    raise SystemExit(main())
