"""PNG export for LabRF spectrum / waterfall (matplotlib Agg; no UI required).

Honest educational exports: titles note mock/synthetic provenance when asked.
Receive-only — no TX, no hardware-verified claims.
"""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from labrf.waterfall import WaterfallBuffer
from spectrum_core.spectrum import Spectrum

PathLike = str | Path


def _as_path_or_file(path_or_file: PathLike | BinaryIO):
    if hasattr(path_or_file, "write"):
        return path_or_file
    return Path(path_or_file)


def export_spectrum_png(
    spectrum: Spectrum,
    path_or_file: PathLike | BinaryIO,
    *,
    peak_hold: Spectrum | None = None,
    peaks: list | None = None,
    threshold_db: float | None = None,
    dpi: int = 120,
    honesty_note: str = "Educational / mock IQ — receive-only; not hardware-verified",
) -> Path | None:
    """Save a spectrum line plot (optional peak-hold overlay) as PNG.

    Returns a ``Path`` when ``path_or_file`` is a filesystem path, else ``None``
    (caller owns the file-like object).
    """
    fig, ax = plt.subplots(figsize=(8.0, 3.6))
    ax.plot(spectrum.x, spectrum.y, lw=1.2, label="Power", color="#1f77b4")
    if peak_hold is not None and len(peak_hold) == len(spectrum):
        ax.plot(
            peak_hold.x,
            peak_hold.y,
            lw=1.0,
            ls="--",
            color="#d62728",
            label="Peak-hold / max-hold",
            alpha=0.9,
        )
    if peaks:
        ax.scatter(
            [p.x for p in peaks[:20]],
            [p.y for p in peaks[:20]],
            s=28,
            c="#d62728",
            marker="v",
            zorder=5,
            label="Peaks",
        )
    if threshold_db is not None:
        ax.axhline(
            float(threshold_db),
            color="#e67e22",
            ls="--",
            lw=1.0,
            label=f"threshold {float(threshold_db):.1f} dB",
        )
    ax.set_xlabel(f"Frequency ({spectrum.x_unit})")
    ax.set_ylabel(f"Power ({spectrum.y_unit})")
    title = spectrum.title or "RF power spectrum"
    ax.set_title(title)
    if honesty_note:
        fig.text(0.5, 0.01, honesty_note, ha="center", va="bottom", fontsize=8, color="#555")
        fig.subplots_adjust(bottom=0.18)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    target = _as_path_or_file(path_or_file)
    fig.savefig(target, dpi=dpi, format="png")
    plt.close(fig)
    return target if isinstance(target, Path) else None


def export_waterfall_png(
    waterfall: WaterfallBuffer | tuple[np.ndarray, np.ndarray],
    path_or_file: PathLike | BinaryIO,
    *,
    x_unit: str = "MHz",
    dpi: int = 120,
    title: str = "LabRF waterfall (mock / educational)",
    honesty_note: str = "Educational / mock IQ — receive-only; not hardware-verified",
) -> Path | None:
    """Save a waterfall heatmap as PNG from a buffer or ``(x, Z)`` matrix."""
    if isinstance(waterfall, WaterfallBuffer):
        x, z = waterfall.as_matrix()
    else:
        x, z = waterfall
    x = np.asarray(x, dtype=float)
    z = np.asarray(z, dtype=float)
    if z.size == 0:
        raise ValueError("waterfall is empty — capture or stream frames first")

    fig, ax = plt.subplots(figsize=(8.0, 3.2))
    extent = None
    if x.size >= 2:
        extent = [float(x[0]), float(x[-1]), 0, z.shape[0]]
    im = ax.imshow(
        z,
        aspect="auto",
        origin="lower",
        extent=extent,
        cmap="viridis",
        interpolation="nearest",
    )
    fig.colorbar(im, ax=ax, label="dB", fraction=0.046, pad=0.04)
    ax.set_xlabel(f"Frequency ({x_unit})")
    ax.set_ylabel("Frame index (oldest → newest)")
    ax.set_title(title)
    if honesty_note:
        fig.text(0.5, 0.01, honesty_note, ha="center", va="bottom", fontsize=8, color="#555")
        fig.subplots_adjust(bottom=0.18)
    target = _as_path_or_file(path_or_file)
    fig.savefig(target, dpi=dpi, format="png")
    plt.close(fig)
    return target if isinstance(target, Path) else None
