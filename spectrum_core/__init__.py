"""spectrum_core — shared spectrum model, ingest, peaks, baseline for ChemSpec / family."""

from pathlib import Path
from typing import Any

from spectrum_core.spectrum import Spectrum, XUnit, YUnit
from spectrum_core.errors import ProcessingError, SpectrumError
from spectrum_core.ingest import (
    ensure_ascending_x,
    ingest as _ingest_impl,
    ingest_csv,
    ingest_jcamp,
    is_jcamp_path,
    x_direction,
    y_unit_from_header,
)
from spectrum_core.spc import ingest_spc, is_spc_path, write_spc_even_x
from spectrum_core import pipeline_extra as _pipeline_extra  # noqa: F401
from spectrum_core.pipeline_extra import op_derivative
from spectrum_core.peaks import find_peaks, Peak
from spectrum_core.diagnostics import (
    DiagnosticFinding,
    MeasurementDiagnostics,
    diagnose_measurement,
    estimate_snr,
)
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
from spectrum_core.overlay import overlay, stack, subtract_spectra
from spectrum_core.quant import (
    BandIntegral,
    CompareResult,
    band_integral,
    beer_lambert_c,
    compare_spectra,
    convert_spectrum_x,
    crossings,
    derivative_spectrum,
    nm_to_wavenumber,
    series_stats,
    wavenumber_to_nm,
)
from spectrum_core.units import (
    absorbance_to_percent_t,
    can_convert_y,
    convert_spectrum_y,
    percent_t_to_absorbance,
)
from spectrum_core.export_peaks import PEAK_CSV_FIELDS, peaks_to_csv
from spectrum_core.export_png import (
    DEFAULT_HONESTY_NOTE,
    export_spectrum_png,
    export_waterfall_png,
)
from spectrum_core.folder import folder_waterfall, ingest_folder, list_spectrum_files
from spectrum_core.viz3d import SurfaceGrid, spectra_to_surface
from spectrum_core.session import (
    SESSION_FORMAT_VERSION,
    SessionData,
    SessionError,
    compute_analysis_fingerprint,
    compute_raw_data_hash,
    load_session,
    migrate_session_dict,
    save_session,
    session_from_dict,
    session_to_dict,
)
from spectrum_core.processing import (
    PIPELINE_STEPS,
    ProcessingHistory,
    ProcessingStep,
    PipelineState,
    apply_step,
    make_step,
    op_baseline,
    op_despike,
    op_normalize,
    op_smooth,
    replay_history,
)


def ingest(
    path: str | Path,
    *,
    x_col: int | str = 0,
    y_col: int | str = 1,
    x_unit: XUnit = "nm",
    y_unit: YUnit = "intensity",
    title: str | None = None,
    meta: dict[str, Any] | None = None,
    **csv_kwargs: Any,
):
    """Dispatch ``.spc`` here; other suffixes go to ``spectrum_core.ingest``."""
    if is_spc_path(path):
        return ingest_spc(path, title=title, meta=meta)
    return _ingest_impl(
        path,
        x_col=x_col,
        y_col=y_col,
        x_unit=x_unit,
        y_unit=y_unit,
        title=title,
        meta=meta,
        **csv_kwargs,
    )

__all__ = [
    "Spectrum",
    "SpectrumError",
    "ProcessingError",
    "XUnit",
    "YUnit",
    "ingest",
    "ingest_csv",
    "ingest_jcamp",
    "is_jcamp_path",
    "ingest_spc",
    "is_spc_path",
    "write_spc_even_x",
    "ensure_ascending_x",
    "x_direction",
    "y_unit_from_header",
    "find_peaks",
    "Peak",
    "DiagnosticFinding",
    "MeasurementDiagnostics",
    "diagnose_measurement",
    "estimate_snr",
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
    "subtract_spectra",
    "BandIntegral",
    "CompareResult",
    "band_integral",
    "beer_lambert_c",
    "compare_spectra",
    "convert_spectrum_x",
    "crossings",
    "derivative_spectrum",
    "nm_to_wavenumber",
    "series_stats",
    "wavenumber_to_nm",
    "absorbance_to_percent_t",
    "percent_t_to_absorbance",
    "convert_spectrum_y",
    "can_convert_y",
    "peaks_to_csv",
    "PEAK_CSV_FIELDS",
    "DEFAULT_HONESTY_NOTE",
    "export_spectrum_png",
    "export_waterfall_png",
    "list_spectrum_files",
    "ingest_folder",
    "folder_waterfall",
    "SurfaceGrid",
    "spectra_to_surface",
    "SESSION_FORMAT_VERSION",
    "SessionData",
    "SessionError",
    "save_session",
    "load_session",
    "session_to_dict",
    "session_from_dict",
    "migrate_session_dict",
    "compute_analysis_fingerprint",
    "compute_raw_data_hash",
    "ProcessingStep",
    "ProcessingHistory",
    "PipelineState",
    "PIPELINE_STEPS",
    "apply_step",
    "make_step",
    "replay_history",
    "op_baseline",
    "op_smooth",
    "op_despike",
    "op_normalize",
    "op_derivative",
]

__version__ = "0.2.0"
