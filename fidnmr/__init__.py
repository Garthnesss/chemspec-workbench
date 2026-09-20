"""FID / NMR Playground — educational FID→FFT stub (Spectrum Family).

Phase 0 ships **synthetic / mock** paths only: complex FID container,
exponential apodization, FFT + manual phase, Hz/ppm axis →
``spectrum_core.Spectrum``. No live Bruker/Varian drivers, no structure
elucidation, no compound identification.
"""

from fidnmr.fid import FID
from fidnmr.mock_source import DEFAULT_TEACHING_PEAKS_PPM, generate_mock_fid
from fidnmr.process import (
    apodize_exp,
    apply_phase,
    fid_to_spectrum,
    hz_to_ppm,
)

__version__ = "0.1.0"

__all__ = [
    "FID",
    "generate_mock_fid",
    "DEFAULT_TEACHING_PEAKS_PPM",
    "apodize_exp",
    "apply_phase",
    "fid_to_spectrum",
    "hz_to_ppm",
    "__version__",
]
