"""TeachSpec — educational optical teaching spectrometer (software stub).

Phase 0 ships synthetic / mock paths plus an **optional** live UVC OpenCV
backend (``pip install -e ".[teachspec]"``). Docs lock **USB camera (UVC)** as
v1 primary sensor. ``UvcIngestStub`` remains an explicit no-camera placeholder.
Linear CCD/CMOS is Phase 2+. No firm vendor BOM prices; camera path is
intensity vs pixel until the user applies ``teachspec.calibration``.

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
from teachspec.uvc_ingest import (
    OpticalFrameSource,
    UvcIngestStub,
    UvcOpenCvSource,
    extract_row,
    open_uvc_source,
)

__version__ = "0.2.0"

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
    "UvcOpenCvSource",
    "extract_row",
    "open_uvc_source",
    "__version__",
]
