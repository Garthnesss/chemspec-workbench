"""TeachSpec — educational optical teaching spectrometer (software stub).

Phase 0 ships **synthetic / mock** paths only: pixel→nm calibration math and
``OpticalLiveFrame`` → ``spectrum_core.Spectrum`` conversion. Docs lock **USB
camera (UVC)** as v1 primary sensor; live UVC ingest is not Implemented (`teachspec.uvc_ingest.UvcIngestStub` raises ``NotImplementedError``).
Linear CCD/CMOS is Phase 2+. No firm vendor BOM prices; no hardware-verified
wavelength claims.

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
from teachspec.uvc_ingest import OpticalFrameSource, UvcIngestStub, extract_row

__version__ = "0.1.0"

__all__ = [
    "WavelengthCalibration",
    "fit_wavelength_calibration",
    "save_calibration",
    "load_calibration",
    "OpticalLiveFrame",
    "frame_to_spectrum",
    "generate_mock_frame",
    "OpticalFrameSource",
    "UvcIngestStub",
    "extract_row",
    "__version__",
]
