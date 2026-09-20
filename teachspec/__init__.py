"""TeachSpec — educational optical teaching spectrometer (software stub).

Phase 0 ships **synthetic / mock** paths only: pixel→nm calibration math and
``OpticalLiveFrame`` → ``spectrum_core.Spectrum`` conversion. No camera or
linear-CCD drivers, no BOM prices, no hardware-verified claims.

Educational scope only — not compound identification, not lab-grade accuracy.
"""

from teachspec.calibration import (
    WavelengthCalibration,
    fit_wavelength_calibration,
    load_calibration,
    save_calibration,
)
from teachspec.mock_source import generate_mock_frame
from teachspec.optical import OpticalLiveFrame, frame_to_spectrum

__version__ = "0.1.0"

__all__ = [
    "WavelengthCalibration",
    "fit_wavelength_calibration",
    "save_calibration",
    "load_calibration",
    "OpticalLiveFrame",
    "frame_to_spectrum",
    "generate_mock_frame",
    "__version__",
]
