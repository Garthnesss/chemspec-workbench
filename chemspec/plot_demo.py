"""Matplotlib plot demo for synthetic fixtures (offline, no web UI required).

Usage (after pip install -e ".[dev]"):
    python chemspec/plot_demo.py
    python chemspec/plot_demo.py --fixture ir --save /tmp/ir_demo.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from spectrum_core import baseline_polynomial, find_peaks, ingest_csv

_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES = _ROOT / "fixtures"


def _load(fixture: str):
    if fixture == "uvvis":
        return ingest_csv(
            _FIXTURES / "uvvis_synthetic.csv",
            x_col="wavelength_nm",
            y_col="absorbance",
            x_unit="nm",
            y_unit="A",
        ), 0.15
    if fixture == "ir":
        return ingest_csv(
            _FIXTURES / "ir_synthetic.csv",
            x_col="wavenumber_cm-1",
            y_col="intensity",
            x_unit="cm-1",
            y_unit="intensity",
        ), 0.15
    raise ValueError(fixture)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ChemSpec matplotlib plot demo")
    parser.add_argument("--fixture", choices=("uvvis", "ir"), default="uvvis")
    parser.add_argument("--save", type=Path, default=None, help="save figure instead of show")
    parser.add_argument("--no-show", action="store_true")
    args = parser.parse_args(argv)

    spec, prom = _load(args.fixture)
    corrected = baseline_polynomial(spec, degree=1)
    peaks = find_peaks(corrected, prominence=prom)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(spec.x, spec.y, color="0.6", lw=1.0, label="raw")
    ax.plot(corrected.x, corrected.y, color="C0", lw=1.4, label="baseline-corrected")
    if peaks:
        ax.scatter(
            [p.x for p in peaks],
            [p.y for p in peaks],
            color="C3",
            zorder=5,
            label=f"peaks (n={len(peaks)})",
        )
        for p in peaks[:8]:
            ax.annotate(
                f"{p.x:.0f}",
                (p.x, p.y),
                textcoords="offset points",
                xytext=(0, 8),
                ha="center",
                fontsize=8,
            )

    xlabel = "Wavelength (nm)" if spec.x_unit == "nm" else "Wavenumber (cm⁻¹)"
    ylabel = {"A": "Absorbance", "percent_T": "%T", "intensity": "Intensity"}[spec.y_unit]
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(f"ChemSpec demo — {spec.title} (synthetic)")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    if spec.x_unit == "cm-1":
        ax.invert_xaxis()  # IR convention
    fig.tight_layout()

    if args.save:
        fig.savefig(args.save, dpi=120)
        print(f"saved {args.save}")
    if not args.no_show and not args.save:
        plt.show()
    elif args.save and not args.no_show:
        pass
    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
