"""spectrum_core — shared spectrum model, ingest, peaks, baseline for ChemSpec / family."""

from spectrum_core.spectrum import Spectrum, XUnit, YUnit
from spectrum_core.ingest import ingest, ingest_csv, ingest_jcamp, is_jcamp_path
from spectrum_core.peaks import find_peaks, Peak
from spectrum_core.baseline import (
    ALL_BASELINE_METHODS,
    METHOD_ASLS,
    METHOD_MPLS,
    METHOD_POLYNOMIAL,
    PYBASELINES_METHODS,
    available_baseline_methods,
    baseline_correct,
    baseline_polynomial,
    has_pybaselines,
)
from spectrum_core.overlay import overlay, stack
from spectrum_core.units import (
    absorbance_to_percent_t,
    can_convert_y,
    convert_spectrum_y,
    percent_t_to_absorbance,
)
from spectrum_core.export_peaks import PEAK_CSV_FIELDS, peaks_to_csv
from spectrum_core.folder import folder_waterfall, ingest_folder, list_spectrum_files
from spectrum_core.session import (
    SESSION_FORMAT_VERSION,
    SessionData,
    SessionError,
    load_session,
    save_session,
    session_from_dict,
    session_to_dict,
)

__all__ = [
    "Spectrum",
    "XUnit",
    "YUnit",
    "ingest",
    "ingest_csv",
    "ingest_jcamp",
    "is_jcamp_path",
    "find_peaks",
    "Peak",
    "baseline_polynomial",
    "baseline_correct",
    "available_baseline_methods",
    "has_pybaselines",
    "METHOD_POLYNOMIAL",
    "METHOD_ASLS",
    "METHOD_MPLS",
    "PYBASELINES_METHODS",
    "ALL_BASELINE_METHODS",
    "overlay",
    "stack",
    "absorbance_to_percent_t",
    "percent_t_to_absorbance",
    "convert_spectrum_y",
    "can_convert_y",
    "peaks_to_csv",
    "PEAK_CSV_FIELDS",
    "list_spectrum_files",
    "ingest_folder",
    "folder_waterfall",
    "SESSION_FORMAT_VERSION",
    "SessionData",
    "SessionError",
    "save_session",
    "load_session",
    "session_to_dict",
    "session_from_dict",
]

__version__ = "0.1.0"
