"""Measurement diagnostics: SNR estimate and peak/baseline warnings.

Honesty: these are **geometric / statistical heuristics** on the loaded trace —
not compound identification, not instrument qualification, and not a claim of
analytical detection limits (LOD) or instrument qualification. Callers should
surface messages as advisory.

**SNR caveat.** ``estimate_snr`` uses MAD of first differences
(``mad_of_first_differences``). On dense, smooth library IR (e.g. public PNNL
JCAMP) structured sample-to-sample Δy is tiny relative to peak prominence, so
the numeric SNR can read **very high** (10³–10⁶). Treat the number as a relative
heuristic for the loaded trace — never as a reported analytical SNR.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np

from spectrum_core.peaks import Peak
from spectrum_core.spectrum import Spectrum

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"

SNR_METHOD_MAD_DIFF = "mad_of_first_differences"
SNR_METHOD_UNAVAILABLE = "unavailable"
# Friendlier strip label (method tag above stays stable for callers/tests).
SNR_DISPLAY_MAD_DIFF = "heuristic MAD-Δy"
# Appended when MAD-Δy SNR is finite; dense/smooth IR often inflates the number.
SNR_HEURISTIC_NOTE = (
    "MAD-Δy heuristic — can read very high on dense/smooth IR (e.g. PNNL); "
    "not LOD/qualification"
)

CODE_LOW_SNR = "low_snr"
CODE_MISSING_LEFT_BOUNDARY = "missing_left_boundary"
CODE_MISSING_RIGHT_BOUNDARY = "missing_right_boundary"
CODE_MISSING_BOTH_BOUNDARIES = "missing_both_boundaries"
CODE_EDGE_PEAK = "edge_peak"
CODE_NAN_FWHM = "nan_fwhm"
CODE_BASELINE_NAN_RESIDUAL = "baseline_nan_residual"
CODE_BASELINE_APPLIED = "baseline_applied"
CODE_NO_FINITE = "no_finite_y"
CODE_ZERO_NOISE = "zero_noise_floor"


def _finite(v: float) -> bool:
    return bool(np.isfinite(v))


@dataclass(frozen=True)
class DiagnosticFinding:
    """One advisory finding (warning or info) about a measurement."""

    code: str
    severity: str
    message: str
    peak_index: int | None = None


@dataclass(frozen=True)
class MeasurementDiagnostics:
    """Bundled SNR estimate + advisory findings for UI / callers."""

    snr_estimate: float = float("nan")
    snr_method: str = SNR_METHOD_UNAVAILABLE
    findings: tuple[DiagnosticFinding, ...] = field(default_factory=tuple)
    peak_count: int = 0

    @property
    def warnings(self) -> list[DiagnosticFinding]:
        return [f for f in self.findings if f.severity == SEVERITY_WARNING]

    @property
    def infos(self) -> list[DiagnosticFinding]:
        return [f for f in self.findings if f.severity == SEVERITY_INFO]

    def summary_line(self, *, max_items: int = 4) -> str:
        """Compact one-line strip for status UIs.

        Labels MAD-Δy SNR as a **heuristic** and notes that dense/smooth IR
        (e.g. PNNL library traces) can inflate the numeric value.
        """
        parts: list[str] = []
        method_disp = (
            SNR_DISPLAY_MAD_DIFF
            if self.snr_method == SNR_METHOD_MAD_DIFF
            else self.snr_method
        )
        # +inf is a valid MAD-Δy outcome (zero noise floor) — do not label as n/a.
        if _finite(self.snr_estimate):
            parts.append(f"SNR≈{self.snr_estimate:.1f} ({method_disp})")
            if self.snr_method == SNR_METHOD_MAD_DIFF:
                parts.append(SNR_HEURISTIC_NOTE)
        elif self.snr_estimate == float("inf"):
            parts.append(f"SNR≈inf ({method_disp})")
            if self.snr_method == SNR_METHOD_MAD_DIFF:
                parts.append(SNR_HEURISTIC_NOTE)
        elif self.snr_method != SNR_METHOD_UNAVAILABLE:
            parts.append(f"SNR=n/a ({method_disp})")
        warns = self.warnings
        if warns:
            shown = warns[:max_items]
            parts.append(
                "warnings: " + "; ".join(f.message for f in shown)
            )
            extra = len(warns) - len(shown)
            if extra > 0:
                parts.append(f"+{extra} more")
        infos = [f for f in self.infos if f.code == CODE_BASELINE_APPLIED]
        for info in infos[:1]:
            parts.append(info.message)
        return " · ".join(parts) if parts else ""


def estimate_noise_mad_diff(y: np.ndarray) -> float:
    """Robust noise floor from MAD of first differences (scale ≈ σ for white noise).

    ``noise = 1.4826 * MAD(Δy) / √2`` — the ``/√2`` accounts for differencing
    of independent samples. Returns ``nan`` when fewer than 3 finite samples.
    """
    y = np.asarray(y, dtype=float)
    finite = y[np.isfinite(y)]
    if finite.size < 3:
        return float("nan")
    diff = np.diff(finite)
    if diff.size == 0:
        return float("nan")
    med = float(np.median(diff))
    mad = float(np.median(np.abs(diff - med)))
    if mad == 0.0:
        # Flat or quantized — try absolute scale of diffs
        scale = float(np.median(np.abs(diff)))
        if scale == 0.0:
            return 0.0
        mad = scale
    # 1.4826 converts MAD→σ for Gaussian; /√2 undoes differencing inflation
    return 1.4826 * mad / np.sqrt(2.0)


def estimate_snr(
    spectrum: Spectrum,
    peaks: Sequence[Peak] | None = None,
) -> tuple[float, str]:
    """Estimate SNR as (signal / noise) with an explicit method tag.

    Signal preference: max peak prominence when peaks are provided and finite;
    else ``nanmax(y) - nanmedian(y)``. Noise: MAD of first differences.

    Returns ``(nan, unavailable)`` when the estimate cannot be formed.
    """
    y = np.asarray(spectrum.y, dtype=float)
    if not np.isfinite(y).any():
        return float("nan"), SNR_METHOD_UNAVAILABLE

    noise = estimate_noise_mad_diff(y)
    if not _finite(noise):
        return float("nan"), SNR_METHOD_UNAVAILABLE

    signal = float("nan")
    if peaks:
        proms = [float(p.prominence) for p in peaks if _finite(float(p.prominence))]
        if proms:
            signal = max(proms)
    if not _finite(signal) or signal <= 0:
        finite = y[np.isfinite(y)]
        if finite.size == 0:
            return float("nan"), SNR_METHOD_UNAVAILABLE
        signal = float(np.nanmax(finite) - np.nanmedian(finite))
    if not _finite(signal) or signal <= 0:
        return float("nan"), SNR_METHOD_UNAVAILABLE
    if noise == 0.0:
        # Perfectly flat noise floor with nonzero signal — treat as very high SNR
        return float("inf"), SNR_METHOD_MAD_DIFF
    return float(signal / noise), SNR_METHOD_MAD_DIFF


def peak_boundary_findings(
    peaks: Sequence[Peak],
    *,
    n_points: int | None = None,
) -> list[DiagnosticFinding]:
    """Warnings for missing half-max crossings / edge peaks / NaN FWHM."""
    out: list[DiagnosticFinding] = []
    for p in peaks:
        left_ok = _finite(float(p.left_boundary_x))
        right_ok = _finite(float(p.right_boundary_x))
        fwhm_ok = _finite(float(p.fwhm))
        near_edge = False
        if n_points is not None and n_points > 0:
            near_edge = p.index <= 1 or p.index >= n_points - 2

        if not left_ok and not right_ok:
            out.append(
                DiagnosticFinding(
                    code=CODE_MISSING_BOTH_BOUNDARIES,
                    severity=SEVERITY_WARNING,
                    message=(
                        f"peak @ x={p.x:.4g}: missing both half-max crossings "
                        "(FWHM/area = NaN)"
                    ),
                    peak_index=p.index,
                )
            )
        elif not left_ok:
            out.append(
                DiagnosticFinding(
                    code=CODE_MISSING_LEFT_BOUNDARY,
                    severity=SEVERITY_WARNING,
                    message=(
                        f"peak @ x={p.x:.4g}: missing left half-max crossing "
                        "(edge, plateau, or NaN)"
                    ),
                    peak_index=p.index,
                )
            )
        elif not right_ok:
            out.append(
                DiagnosticFinding(
                    code=CODE_MISSING_RIGHT_BOUNDARY,
                    severity=SEVERITY_WARNING,
                    message=(
                        f"peak @ x={p.x:.4g}: missing right half-max crossing "
                        "(edge, plateau, or NaN)"
                    ),
                    peak_index=p.index,
                )
            )
        elif not fwhm_ok:
            out.append(
                DiagnosticFinding(
                    code=CODE_NAN_FWHM,
                    severity=SEVERITY_WARNING,
                    message=f"peak @ x={p.x:.4g}: FWHM is NaN despite boundaries",
                    peak_index=p.index,
                )
            )

        if near_edge and (not left_ok or not right_ok):
            out.append(
                DiagnosticFinding(
                    code=CODE_EDGE_PEAK,
                    severity=SEVERITY_INFO,
                    message=(
                        f"peak @ x={p.x:.4g}: near spectrum edge "
                        f"(index={p.index})"
                    ),
                    peak_index=p.index,
                )
            )
    return out


def baseline_findings(
    spectrum: Spectrum,
    *,
    baseline_applied: bool = False,
) -> list[DiagnosticFinding]:
    """Advisory findings when a baseline was applied or is present in meta."""
    out: list[DiagnosticFinding] = []
    meta = spectrum.meta or {}
    method = meta.get("baseline_method")
    applied = baseline_applied or bool(method)
    if not applied:
        return out

    method_s = str(method) if method else "on"
    out.append(
        DiagnosticFinding(
            code=CODE_BASELINE_APPLIED,
            severity=SEVERITY_INFO,
            message=f"baseline applied ({method_s})",
        )
    )

    y = np.asarray(spectrum.y, dtype=float)
    n = y.size
    if n == 0:
        return out
    n_bad = int(np.count_nonzero(~np.isfinite(y)))
    if n_bad > 0:
        frac = n_bad / n
        out.append(
            DiagnosticFinding(
                code=CODE_BASELINE_NAN_RESIDUAL,
                severity=SEVERITY_WARNING,
                message=(
                    f"baseline residual has {n_bad}/{n} non-finite y "
                    f"({frac:.0%}) — check fit mask / method"
                ),
            )
        )
    return out


def diagnose_measurement(
    spectrum: Spectrum | None,
    peaks: Sequence[Peak] | Iterable[Peak] | None = None,
    *,
    baseline_applied: bool = False,
    low_snr_threshold: float = 3.0,
) -> MeasurementDiagnostics:
    """Run SNR + peak boundary + baseline diagnostics.

    Parameters
    ----------
    spectrum :
        Working (display) spectrum, or ``None`` → empty diagnostics.
    peaks :
        Peaks characterized on that spectrum (optional).
    baseline_applied :
        True when the UI / pipeline has a baseline step active even if meta
        does not yet record ``baseline_method``.
    low_snr_threshold :
        Emit a ``low_snr`` warning when finite SNR is below this value.
    """
    if spectrum is None:
        return MeasurementDiagnostics()

    peak_list: list[Peak] = list(peaks) if peaks is not None else []
    findings: list[DiagnosticFinding] = []

    y = np.asarray(spectrum.y, dtype=float)
    if not np.isfinite(y).any():
        findings.append(
            DiagnosticFinding(
                code=CODE_NO_FINITE,
                severity=SEVERITY_WARNING,
                message="no finite y samples — cannot estimate SNR or peaks",
            )
        )
        return MeasurementDiagnostics(
            snr_estimate=float("nan"),
            snr_method=SNR_METHOD_UNAVAILABLE,
            findings=tuple(findings),
            peak_count=len(peak_list),
        )

    snr, method = estimate_snr(spectrum, peak_list)
    if _finite(snr) and snr < low_snr_threshold:
        findings.append(
            DiagnosticFinding(
                code=CODE_LOW_SNR,
                severity=SEVERITY_WARNING,
                message=(
                    f"low SNR estimate ({snr:.1f} < {low_snr_threshold:g}; "
                    f"method={method})"
                ),
            )
        )
    elif snr == 0.0:
        findings.append(
            DiagnosticFinding(
                code=CODE_ZERO_NOISE,
                severity=SEVERITY_INFO,
                message="noise floor estimate is zero (flat / quantized trace)",
            )
        )

    findings.extend(peak_boundary_findings(peak_list, n_points=len(spectrum)))
    findings.extend(
        baseline_findings(spectrum, baseline_applied=baseline_applied)
    )

    return MeasurementDiagnostics(
        snr_estimate=snr,
        snr_method=method,
        findings=tuple(findings),
        peak_count=len(peak_list),
    )


__all__ = [
    "CODE_BASELINE_APPLIED",
    "CODE_BASELINE_NAN_RESIDUAL",
    "CODE_EDGE_PEAK",
    "CODE_LOW_SNR",
    "CODE_MISSING_BOTH_BOUNDARIES",
    "CODE_MISSING_LEFT_BOUNDARY",
    "CODE_MISSING_RIGHT_BOUNDARY",
    "CODE_NAN_FWHM",
    "CODE_NO_FINITE",
    "CODE_ZERO_NOISE",
    "DiagnosticFinding",
    "MeasurementDiagnostics",
    "SEVERITY_INFO",
    "SEVERITY_WARNING",
    "SNR_DISPLAY_MAD_DIFF",
    "SNR_HEURISTIC_NOTE",
    "SNR_METHOD_MAD_DIFF",
    "SNR_METHOD_UNAVAILABLE",
    "baseline_findings",
    "diagnose_measurement",
    "estimate_noise_mad_diff",
    "estimate_snr",
    "peak_boundary_findings",
]
