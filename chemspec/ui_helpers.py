"""UI-facing helpers (no NiceGUI import — safe for tests without [ui])."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from spectrum_core.spectrum import XUnit, YUnit
_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = _ROOT / "fixtures"

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
}




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
    """
    result: dict[str, Any] = {
        "x_col": 0 if not headers else headers[0],
        "y_col": 1 if len(headers) < 2 else headers[1],
        "x_unit": "nm",
        "y_unit": "intensity",
    }
    if not headers:
        return result

    lower = [h.lower() for h in headers]

    def _find(*needles: str) -> str | None:
        for i, name in enumerate(lower):
            if any(n in name for n in needles):
                return headers[i]
        return None

    x = (
        _find("wavelength", "lambda", "nm")
        or _find("wavenumber", "wave_number", "cm-1", "cm^-1", "cm⁻¹")
        or _find("x")
    )
    y = (
        _find("absorbance", "abs", "od")
        or _find("transmittance", "percent_t", "%t", "pct_t")
        or _find("intensity", "signal", "counts", "y")
    )
    if x is not None:
        result["x_col"] = x
        xl = x.lower()
        if any(k in xl for k in ("wavenumber", "cm-1", "cm^-1", "cm⁻¹")):
            result["x_unit"] = "cm-1"
        else:
            result["x_unit"] = "nm"
    if y is not None:
        result["y_col"] = y
        yl = y.lower()
        if any(k in yl for k in ("absorbance", "abs", "od")):
            result["y_unit"] = "A"
        elif any(k in yl for k in ("transmittance", "%t", "percent_t", "pct_t")):
            result["y_unit"] = "percent_T"
        else:
            result["y_unit"] = "intensity"
    return result


def axis_label(x_unit: XUnit, y_unit: YUnit) -> tuple[str, str]:
    xlabel = "Wavelength (nm)" if x_unit == "nm" else "Wavenumber (cm⁻¹)"
    ylabel = {
        "A": "Absorbance",
        "percent_T": "%T",
        "intensity": "Intensity",
    }[y_unit]
    return xlabel, ylabel
