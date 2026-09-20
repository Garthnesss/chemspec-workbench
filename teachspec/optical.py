"""Optical live-frame adapter: 1-D intensity → spectrum_core.Spectrum.

Mock and calibrated paths work without camera libraries. Live UVC frames
(optional ``[teachspec]`` OpenCV extra) also land here as ``OpticalLiveFrame``
via ``teachspec.uvc_ingest.UvcOpenCvSource``. Wavelength axes still require
``teachspec.calibration`` — the camera alone is not nm-calibrated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from spectrum_core import Spectrum
from teachspec.calibration import WavelengthCalibration


@dataclass
class OpticalLiveFrame:
    """One 1-D intensity row from a teaching spectrometer sensor.

    ``intensity`` is arbitrary relative units (counts / ADU). Pixel index 0
    is the first sample. Metadata should mark ``synthetic=True`` for mock
    frames so UIs never imply a live hardware capture.
    """

    intensity: np.ndarray
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.intensity = np.asarray(self.intensity, dtype=float)
        if self.intensity.ndim != 1:
            raise ValueError("intensity must be a 1-D array")
        if self.intensity.size == 0:
            raise ValueError("intensity must have at least one sample")


def frame_to_spectrum(
    frame: OpticalLiveFrame,
    calibration: WavelengthCalibration,
    *,
    title: str = "",
    y_unit: str = "intensity",
) -> Spectrum:
    """Apply pixel→nm calibration and return a ``Spectrum`` (x in nm).

    Does not identify compounds. Wavelength uncertainty is whatever the
    calibration documents (fit residuals only in Phase 0).
    """
    n = frame.intensity.size
    pixels = np.arange(n, dtype=float)
    x_nm = calibration.pixel_to_nm(pixels)
    meta = {
        **dict(frame.meta),
        "teachspec_calibration": {
            "fit_kind": calibration.fit_kind,
            "coefficients": list(calibration.coefficients),
            "rmse_nm": calibration.rmse_nm,
            "max_abs_residual_nm": calibration.max_abs_residual_nm,
        },
        "source": frame.meta.get("source", "teachspec.optical.frame_to_spectrum"),
    }
    return Spectrum(
        x=x_nm,
        y=frame.intensity.copy(),
        x_unit="nm",
        y_unit=y_unit,  # type: ignore[arg-type]
        title=title or str(frame.meta.get("title", "TeachSpec frame")),
        meta=meta,
    )
