"""LabRF Monitor — receive-only RF spectrum / waterfall on spectrum_core.

Educational / EMI situational awareness. Not chemical ID, not regulatory advice,
not a transmitter.
"""

from labrf.events import ThresholdEvent, ThresholdEventLog, evaluate_threshold
from labrf.export_png import export_spectrum_png, export_waterfall_png
from labrf.peak_hold import PeakHoldTracker
from labrf.fft_spectrum import iq_to_spectrum
from labrf.iq import generate_synthetic_iq, load_iq_fixture
from labrf.presets import PRESETS_DISCLAIMER, load_presets
from labrf.stream import MockStreamGenerator, format_labrf_provenance
from labrf.waterfall import WaterfallBuffer

__version__ = "0.2.0"

__all__ = [
    "generate_synthetic_iq",
    "load_iq_fixture",
    "iq_to_spectrum",
    "WaterfallBuffer",
    "PeakHoldTracker",
    "export_spectrum_png",
    "export_waterfall_png",
    "load_presets",
    "PRESETS_DISCLAIMER",
    "ThresholdEvent",
    "ThresholdEventLog",
    "evaluate_threshold",
    "MockStreamGenerator",
    "format_labrf_provenance",
    "__version__",
]
