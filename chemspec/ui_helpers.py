"""UI-facing helpers (no NiceGUI import — safe for tests without [ui])."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from spectrum_core.spectrum import XUnit, YUnit

_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = _ROOT / "fixtures"
PUBLIC_FIXTURES_DIR = FIXTURES_DIR / "public"
WATERFALL_FIXTURE_DIR = FIXTURES_DIR / "waterfall"

FIXTURE_PRESETS: dict[str, dict[str, Any]] = {
    "uvvis": {
        "label": "UV-Vis synthetic",
        "path": FIXTURES_DIR / "uvvis_synthetic.csv",
        "x_col": "wavelength_nm",
        "y_col": "absorbance",
        "x_unit": "nm",
        "y_unit": "A",
        "prominence": 0.15,
        "baseline_degree": 1,
    },
    "ir": {
        "label": "IR synthetic",
        "path": FIXTURES_DIR / "ir_synthetic.csv",
        "x_col": "wavenumber_cm-1",
        "y_col": "intensity",
        "x_unit": "cm-1",
        "y_unit": "intensity",
        "prominence": 0.15,
        "baseline_degree": 1,
    },
    "uvvis_jcamp": {
        "label": "UV-Vis JCAMP synthetic",
        "path": FIXTURES_DIR / "uvvis_synthetic.jdx",
        "format": "jcamp",
        "prominence": 0.15,
        "baseline_degree": 1,
    },
    "ir_jcamp": {
        "label": "IR JCAMP synthetic",
        "path": FIXTURES_DIR / "ir_synthetic.dx",
        "format": "jcamp",
        "prominence": 0.15,
        "baseline_degree": 1,
    },
    "public_ethanol_ir": {
        "label": "Public: Ethanol IR (PNNL / NIST)",
        "path": PUBLIC_FIXTURES_DIR / "ethanol_ir_pnnl.jdx",
        "format": "jcamp",
        "kind": "public",
        "prominence": 0.05,
        "baseline_degree": 1,
    },
    "public_methanol_ir": {
        "label": "Public: Methanol IR (PNNL / NIST)",
        "path": PUBLIC_FIXTURES_DIR / "methanol_ir_pnnl.jdx",
        "format": "jcamp",
        "kind": "public",
        "prominence": 0.05,
        "baseline_degree": 1,
    },
    "public_toluene_ir": {
        "label": "Public: Toluene IR (PNNL / NIST)",
        "path": PUBLIC_FIXTURES_DIR / "toluene_ir_pnnl.jdx",
        "format": "jcamp",
        "kind": "public",
        "prominence": 0.05,
        "baseline_degree": 1,
    },
    "public_benzene_uvvis": {
        "label": "Public: Benzene UV-Vis (NIST)",
        "path": PUBLIC_FIXTURES_DIR / "benzene_uvvis_nist.jdx",
        "format": "jcamp",
        "kind": "public",
        "prominence": 0.05,
        "baseline_degree": 1,
    },
    "public_acetone_uvvis": {
        "label": "Public: Acetone UV-Vis (NIST)",
        "path": PUBLIC_FIXTURES_DIR / "acetone_uvvis_nist.jdx",
        "format": "jcamp",
        "kind": "public",
        "prominence": 0.05,
        "baseline_degree": 1,
    },
    "public_naphthalene_uvvis": {
        "label": "Public: Naphthalene UV-Vis (NIST)",
        "path": PUBLIC_FIXTURES_DIR / "naphthalene_uvvis_nist.jdx",
        "format": "jcamp",
        "kind": "public",
        "prominence": 0.05,
        "baseline_degree": 1,
    },
}

_TOKEN_RE = re.compile(r"[a-z0-9%]+", re.IGNORECASE)


def _tokens(name: str) -> set[str]:
    """Alphanumeric tokens from a header (lowercased)."""
    return {m.group(0).lower() for m in _TOKEN_RE.finditer(name)}


def _is_absorbance_header(name: str) -> bool:
    """True when a column name clearly means absorbance (A), not intensity.

    Uses substring matches for long forms and *exact tokens* for short
    aliases (``A``, ``Abs``, ``AU``, ``OD``) so ``absolute_intensity`` is
    not mis-tagged as absorbance.
    """
    low = name.lower()
    if "absorbance" in low or "optical density" in low or "optical_density" in low:
        return True
    return bool(_tokens(name) & {"a", "abs", "au", "od"})


def _is_transmittance_header(name: str) -> bool:
    low = name.lower()
    if "transmittance" in low or "transmission" in low:
        return True
    return bool(_tokens(name) & {"percent_t", "pct_t", "%t", "t%"})


def _is_intensity_header(name: str) -> bool:
    low = name.lower()
    if "intensity" in low or "counts" in low or "signal" in low:
        return True
    # Exact token "y" only — avoid matching inside unrelated words.
    return "y" in _tokens(name) and not _is_absorbance_header(name)


def _is_wavenumber_header(name: str) -> bool:
    low = name.lower()
    if "wavenumber" in low or "wave_number" in low:
        return True
    toks = _tokens(name)
    return bool(toks & {"cm-1", "cm1"}) or "cm^-1" in low or "cm⁻¹" in name


def _is_wavelength_header(name: str) -> bool:
    low = name.lower()
    if "wavelength" in low or "lambda" in low:
        return True
    toks = _tokens(name)
    # bare "nm" token; avoid treating every header with "nm" substring oddly
    return "nm" in toks


def sniff_csv_header(path: Path | str) -> list[str]:
    """Return header column names, or empty list if the first data line is numeric."""
    path = Path(path)
    with path.open(newline="") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped or stripped.lstrip().startswith("#"):
                continue
            # sniff delimiter like ingest
            if "\t" in stripped and stripped.count("\t") >= stripped.count(","):
                delim = "\t"
            elif "," in stripped:
                delim = ","
            elif ";" in stripped:
                delim = ";"
            else:
                delim = ","
            fields = [c.strip() for c in stripped.split(delim)]
            try:
                for f in fields:
                    float(f)
                return []  # numeric first row → no header names
            except ValueError:
                return fields
    return []


def guess_column_mapping(headers: list[str]) -> dict[str, Any]:
    """Heuristic x/y column + unit guess from header names.

    Falls back to indices 0/1 when headers are empty or unmatched.

    Absorbance columns (``absorbance``, ``Abs``, ``A``, ``AU``, ``OD``, …)
    map to ``y_unit='A'`` so A↔%T works. IR-style ``intensity`` stays
    ``intensity`` unless the header is clearly %T/A.
    """
    result: dict[str, Any] = {
        "x_col": 0 if not headers else headers[0],
        "y_col": 1 if len(headers) < 2 else headers[1],
        "x_unit": "nm",
        "y_unit": "intensity",
    }
    if not headers:
        return result

    def _find(pred) -> str | None:  # noqa: ANN001
        for h in headers:
            if pred(h):
                return h
        return None

    x = (
        _find(_is_wavelength_header)
        or _find(_is_wavenumber_header)
        or _find(lambda h: "x" in _tokens(h))
    )
    y = (
        _find(_is_absorbance_header)
        or _find(_is_transmittance_header)
        or _find(_is_intensity_header)
    )
    if x is not None:
        result["x_col"] = x
        if _is_wavenumber_header(x):
            result["x_unit"] = "cm-1"
        else:
            result["x_unit"] = "nm"
    if y is not None:
        result["y_col"] = y
        if _is_absorbance_header(y):
            result["y_unit"] = "A"
        elif _is_transmittance_header(y):
            result["y_unit"] = "percent_T"
        else:
            result["y_unit"] = "intensity"
    elif len(headers) >= 2:
        # Second column present but unmatched — still prefer absorbance token
        # check on the default y column so "A" / "AU" headers are not left as
        # intensity (which blocks A↔%T in the UI).
        y_default = headers[1]
        if _is_absorbance_header(y_default):
            result["y_col"] = y_default
            result["y_unit"] = "A"
        elif _is_transmittance_header(y_default):
            result["y_col"] = y_default
            result["y_unit"] = "percent_T"
    return result


def axis_label(x_unit: XUnit, y_unit: YUnit) -> tuple[str, str]:
    xlabel = "Wavelength (nm)" if x_unit == "nm" else "Wavenumber (cm⁻¹)"
    ylabel = {
        "A": "Absorbance",
        "percent_T": "%T",
        "intensity": "Intensity",
    }[y_unit]
    return xlabel, ylabel


def peak_export_filename(title: str | None = None) -> str:
    """Safe download basename for a peak-table CSV."""
    stem = (title or "").strip()
    if not stem:
        return "peaks.csv"
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in stem)
    return f"{safe}_peaks.csv"


def format_provenance(
    *,
    source: str | Path | None,
    x_unit: str | None,
    y_unit: str | None,
    baseline_method: str | None,
    peak_count: int,
    package_version: str | None = None,
    title: str | None = None,
) -> str:
    """Build a one-line provenance strip for the NiceGUI status area.

    Parameters
    ----------
    source :
        File path or name (basename shown when a path is given).
    x_unit, y_unit :
        Axis unit tags (e.g. ``nm`` / ``A``).
    baseline_method :
        Active baseline method name, or ``None`` / empty when off.
    peak_count :
        Number of peaks currently shown.
    package_version :
        Optional ``chemspec-workbench`` / ``spectrum_core`` version string.
    title :
        Optional spectrum title (shown when no source path).
    """
    if source:
        src_path = Path(str(source))
        src_bit = src_path.name or str(source)
    elif title:
        src_bit = title
    else:
        src_bit = "(no source)"

    xu = x_unit or "?"
    yu = y_unit or "?"
    bl = baseline_method.strip() if baseline_method else ""
    bl_bit = bl if bl else "none"
    parts = [
        f"source={src_bit}",
        f"x={xu}",
        f"y={yu}",
        f"baseline={bl_bit}",
        f"peaks={int(peak_count)}",
    ]
    if package_version:
        parts.append(f"v={package_version}")
    return " · ".join(parts)


def provenance_from_state(
    *,
    primary_path: str | None,
    spectrum_title: str | None,
    x_unit: str | None,
    y_unit: str | None,
    baseline_on: bool,
    baseline_method: str | None,
    peak_count: int,
    package_version: str | None = None,
) -> str:
    """Convenience wrapper: map UI state fields → ``format_provenance``."""
    active_bl = baseline_method if baseline_on else None
    return format_provenance(
        source=primary_path,
        title=spectrum_title,
        x_unit=x_unit,
        y_unit=y_unit,
        baseline_method=active_bl,
        peak_count=peak_count,
        package_version=package_version,
    )
