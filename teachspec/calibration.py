"""Pixel → wavelength (nm) calibration for TeachSpec.

Fit a linear (default) or optional quadratic map from detector pixel indices
to nanometers using ≥2 known emission lines (e.g. teaching CFL / Hg lines).

Uncertainty notes
-----------------
This module stores residual statistics (RMSE, max abs residual) from the fit
points only. It does **not** propagate line-assignment error, slit width,
sensor nonlinearity, or temperature drift. Treat reported residuals as a
lower bound on classroom uncertainty — never claim lab-grade accuracy or
hardware-verified performance from software alone.

Educational use only; not compound identification.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal, Sequence

import numpy as np

FitKind = Literal["linear", "quadratic"]


@dataclass
class WavelengthCalibration:
    """Pixel→nm polynomial calibration (degree 1 or 2).

    ``coefficients`` are highest-degree first (numpy ``polyfit`` / ``polyval``
    convention): linear ``[a, b]`` → ``nm = a*pixel + b``; quadratic
    ``[a, b, c]`` → ``nm = a*pixel**2 + b*pixel + c``.
    """

    coefficients: list[float]
    fit_kind: FitKind = "linear"
    known_lines: list[dict[str, float]] = field(default_factory=list)
    rmse_nm: float | None = None
    max_abs_residual_nm: float | None = None
    notes: str = (
        "Educational pixel→nm fit. Residuals are fit-point only; "
        "not hardware-verified; not compound ID."
    )
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        coeffs = [float(c) for c in self.coefficients]
        if self.fit_kind == "linear" and len(coeffs) != 2:
            raise ValueError("linear calibration requires exactly 2 coefficients")
        if self.fit_kind == "quadratic" and len(coeffs) != 3:
            raise ValueError("quadratic calibration requires exactly 3 coefficients")
        if self.fit_kind not in ("linear", "quadratic"):
            raise ValueError(f"unsupported fit_kind: {self.fit_kind!r}")
        self.coefficients = coeffs

    def pixel_to_nm(self, pixels: np.ndarray | Sequence[float]) -> np.ndarray:
        """Map pixel indices to wavelength in nm."""
        x = np.asarray(pixels, dtype=float)
        return np.polyval(self.coefficients, x)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WavelengthCalibration:
        return cls(
            coefficients=list(data["coefficients"]),
            fit_kind=data.get("fit_kind", "linear"),
            known_lines=list(data.get("known_lines", [])),
            rmse_nm=data.get("rmse_nm"),
            max_abs_residual_nm=data.get("max_abs_residual_nm"),
            notes=data.get("notes", WavelengthCalibration.__dataclass_fields__["notes"].default),
            meta=dict(data.get("meta", {})),
        )


def fit_wavelength_calibration(
    pixels: Sequence[float],
    wavelengths_nm: Sequence[float],
    *,
    fit_kind: FitKind = "linear",
    meta: dict[str, Any] | None = None,
) -> WavelengthCalibration:
    """Fit pixel→nm from known line pairs.

    Parameters
    ----------
    pixels:
        Detector pixel indices for known lines (≥2 unique values).
    wavelengths_nm:
        Corresponding wavelengths in nanometers (same length).
    fit_kind:
        ``\"linear\"`` (degree 1, ≥2 points) or ``\"quadratic\"`` (degree 2, ≥3 points).

    Raises
    ------
    ValueError
        Fewer than required points, length mismatch, or duplicate pixels.
    """
    px = np.asarray(pixels, dtype=float).ravel()
    wl = np.asarray(wavelengths_nm, dtype=float).ravel()
    if px.shape != wl.shape:
        raise ValueError(
            f"pixels and wavelengths_nm length mismatch: {px.size} vs {wl.size}"
        )
    if fit_kind == "linear":
        min_pts, degree = 2, 1
    elif fit_kind == "quadratic":
        min_pts, degree = 3, 2
    else:
        raise ValueError(f"unsupported fit_kind: {fit_kind!r}")

    if px.size < min_pts:
        raise ValueError(
            f"{fit_kind} fit needs ≥{min_pts} known lines; got {px.size}"
        )
    if len(np.unique(px)) < px.size:
        raise ValueError("duplicate pixel indices are not allowed for calibration")

    coeffs = np.polyfit(px, wl, deg=degree)
    pred = np.polyval(coeffs, px)
    residuals = wl - pred
    rmse = float(np.sqrt(np.mean(residuals**2)))
    max_abs = float(np.max(np.abs(residuals)))
    known = [
        {"pixel": float(p), "wavelength_nm": float(w)}
        for p, w in zip(px.tolist(), wl.tolist())
    ]
    return WavelengthCalibration(
        coefficients=[float(c) for c in coeffs],
        fit_kind=fit_kind,
        known_lines=known,
        rmse_nm=rmse,
        max_abs_residual_nm=max_abs,
        meta=dict(meta or {}),
    )


def save_calibration(cal: WavelengthCalibration, path: str | Path) -> Path:
    """Write calibration JSON (UTF-8)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = cal.to_dict()
    payload["format"] = "teachspec.calibration"
    payload["format_version"] = 1
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def load_calibration(path: str | Path) -> WavelengthCalibration:
    """Load calibration JSON written by :func:`save_calibration`."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if "coefficients" not in data:
        raise ValueError(f"calibration file missing coefficients: {path}")
    return WavelengthCalibration.from_dict(data)
