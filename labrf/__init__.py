"""LabRF Monitor — receive-only RF spectrum / waterfall on spectrum_core.

Educational / EMI situational awareness. Not chemical ID, not regulatory advice,
not a transmitter.
"""

from labrf.events import ThresholdEvent, ThresholdEventLog, evaluate_threshold
from labrf.fft_spectrum import iq_to_spectrum
from labrf.iq import generate_synthetic_iq, load_iq_fixture
from labrf.presets import PRESETS_DISCLAIMER, load_presets
from labrf.stream import MockStreamGenerator, format_labrf_provenance
from labrf.waterfall import WaterfallBuffer

__version__ = "0.1.0"

__all__ = [
    "generate_synthetic_iq",
    "load_iq_fixture",
    "iq_to_spectrum",
    "WaterfallBuffer",
    "load_presets",
    "PRESETS_DISCLAIMER",
    "ThresholdEvent",
    "ThresholdEventLog",
    "evaluate_threshold",
    "MockStreamGenerator",
    "format_labrf_provenance",
    "__version__",
]
