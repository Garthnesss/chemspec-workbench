"""spectrum_core — shared spectrum model, ingest, peaks, baseline for ChemSpec / family."""

from spectrum_core.spectrum import Spectrum, XUnit, YUnit
from spectrum_core.ingest import ingest, ingest_csv, ingest_jcamp, is_jcamp_path
from spectrum_core.peaks import find_peaks, Peak
from spectrum_core.baseline import baseline_polynomial
from spectrum_core.overlay import overlay, stack

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
    "overlay",
    "stack",
]

__version__ = "0.1.0"
