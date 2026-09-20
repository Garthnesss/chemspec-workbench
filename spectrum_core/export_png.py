"""PNG export for ChemSpec / spectrum_core plots (matplotlib Agg; no UI required).

Honest educational exports: footer notes synthetic/public provenance and
explicitly disclaims compound identification. Parity with LabRF PNG honesty
footer pattern (``labrf.export_png``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, BinaryIO, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from spectrum_core.overlay import stack
from spectrum_core.peaks import Peak
from spectrum_core.spectrum import Spectrum

PathLike = str | Path

DEFAULT_HONESTY_NOTE = (
    "Synthetic/public fixtures labeled as such — ChemSpec makes no compound-ID claims"
)


def _as_path_or_file(path_or_file: PathLike | BinaryIO):
    if hasattr(path_or_file, "write"):
        return path_or_file
    return Path(path_or_file)


def _is_log_epsilon_meta(meta: dict[str, Any] | None) -> bool:
    """True when spectrum meta notes say y is log₁₀(ε), not absorbance."""
    if not meta:
        return False
    notes = meta.get("unit_notes") or []
    if isinstance(notes, str):
        notes = [notes]
    blob = " ".join(str(n) for n in notes).lower()
    if "not absorbance" in blob and ("log" in blob or "ε" in blob or "epsilon" in blob):
        return True
    yunits = str(meta.get("yunits") or meta.get("YUNITS") or meta.get("jcamp_yunits") or "").lower()
    if ("epsilon" in yunits or "ε" in yunits) and "log" in yunits:
        return True
    return False


def _x_label(x_unit: str) -> str:
    return {
        "nm": "Wavelength (nm)",
        "cm-1": "Wavenumber (cm⁻¹)",
        "Hz": "Frequency (Hz)",
        "MHz": "Frequency (MHz)",
    }.get(str(x_unit), f"x ({x_unit})")


def _y_label(y_unit: str, meta: dict[str, Any] | None = None) -> str:
    if _is_log_epsilon_meta(meta):
        return "log₁₀(ε) [intensity — not absorbance]"
    return {
        "A": "Absorbance",
        "percent_T": "%T",
        "intensity": "Intensity",
        "dB": "Power (dB)",
    }.get(str(y_unit), str(y_unit))


def export_spectrum_png(
    spectrum: Spectrum,
    path_or_file: PathLike | BinaryIO,
    *,
    peaks: Sequence[Peak] | None = None,
    overlay: Spectrum | None = None,
    raw: Spectrum | None = None,
    dpi: int = 120,
    title: str | None = None,
    honesty_note: str = DEFAULT_HONESTY_NOTE,
    max_peak_labels: int = 12,
) -> Path | None:
    """Save a spectrum line plot (optional raw/overlay/peaks) as PNG.

    Returns a ``Path`` when ``path_or_file`` is a filesystem path, else ``None``
    (caller owns the file-like object).

    IR convention: ``x_unit == "cm-1"`` reverses the x-axis. Log₁₀(ε) meta
    yields an honest y-axis caption (not absorbance).
    """
    fig, ax = plt.subplots(figsize=(9.0, 4.5))

    if raw is not None and len(raw) > 0:
        ax.plot(
            raw.x,
            raw.y,
            color="0.65",
            lw=1.0,
            label=raw.title or "raw",
            alpha=0.85,
        )

    label = spectrum.title or "spectrum"
    ax.plot(
        spectrum.x,
        spectrum.y,
        color="#1f77b4",
        lw=1.5,
        label=label,
    )

    if overlay is not None and len(overlay) > 0:
        ax.plot(
            overlay.x,
            overlay.y,
            color="#ff7f0e",
            lw=1.3,
            ls="--",
            label=overlay.title or "overlay",
            alpha=0.95,
        )

    if peaks:
        xs = [p.x for p in peaks]
        ys = [p.y for p in peaks]
        ax.scatter(
            xs,
            ys,
            s=36,
            c="#d62728",
            marker="o",
            zorder=5,
            label=f"peaks (n={len(peaks)})",
        )
        for p in list(peaks)[: max(0, int(max_peak_labels))]:
            ax.annotate(
                f"{p.x:.1f}",
                (p.x, p.y),
                textcoords="offset points",
                xytext=(0, 8),
                ha="center",
                fontsize=8,
                color="#d62728",
            )

    ax.set_xlabel(_x_label(spectrum.x_unit))
    ax.set_ylabel(_y_label(spectrum.y_unit, spectrum.meta))
    ax.set_title(title or (spectrum.title or "ChemSpec spectrum"))
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)
    if spectrum.x_unit == "cm-1":
        ax.invert_xaxis()

    if honesty_note:
        fig.text(
            0.5,
            0.01,
            honesty_note,
            ha="center",
            va="bottom",
            fontsize=8,
            color="#555",
        )
        fig.subplots_adjust(bottom=0.18)
    else:
        fig.tight_layout()

    target = _as_path_or_file(path_or_file)
    fig.savefig(target, dpi=dpi, format="png")
    plt.close(fig)
    return target if isinstance(target, Path) else None


def export_waterfall_png(
    spectra: Sequence[Spectrum],
    path_or_file: PathLike | BinaryIO,
    *,
    dpi: int = 120,
    title: str = "ChemSpec — stacked waterfall",
    honesty_note: str = (
        "Stack offsets are for display only — ChemSpec makes no compound-ID claims"
    ),
) -> Path | None:
    """Save a stacked multi-trace waterfall as PNG (display offsets only)."""
    if not spectra:
        raise ValueError("waterfall is empty — load spectra first")

    stacked = stack(list(spectra))
    fig, ax = plt.subplots(figsize=(9.0, 4.5))
    cmap = plt.get_cmap("tab10")
    first = stacked[0]
    for i, spec in enumerate(stacked):
        ax.plot(
            spec.x,
            spec.y,
            lw=1.2,
            color=cmap(i % 10),
            label=spec.title or f"trace_{i}",
        )
    ax.set_xlabel(_x_label(first.x_unit))
    ax.set_ylabel(f"{_y_label(first.y_unit, first.meta)} (+ stack offset)")
    ax.set_title(title)
    ax.legend(loc="best", fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)
    if first.x_unit == "cm-1":
        ax.invert_xaxis()

    if honesty_note:
        fig.text(
            0.5,
            0.01,
            honesty_note,
            ha="center",
            va="bottom",
            fontsize=8,
            color="#555",
        )
        fig.subplots_adjust(bottom=0.18)
    else:
        fig.tight_layout()

    target = _as_path_or_file(path_or_file)
    fig.savefig(target, dpi=dpi, format="png")
    plt.close(fig)
    return target if isinstance(target, Path) else None
