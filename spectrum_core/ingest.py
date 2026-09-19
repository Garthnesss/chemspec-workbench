"""CSV and JCAMP-DX ingest adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from spectrum_core.spectrum import Spectrum, XUnit, YUnit

# JCAMP ##XUNITS / ##YUNITS strings (lowercased, trimmed) → Spectrum units.
# Unknown x units raise; unknown y units fall back to intensity (noted in meta).
_XUNIT_ALIASES: dict[str, XUnit] = {
    "nanometers": "nm",
    "nanometer": "nm",
    "nm": "nm",
    "wavelength": "nm",
    "wavelength in nanometers": "nm",
    "1/cm": "cm-1",
    "1/cm.": "cm-1",
    "cm-1": "cm-1",
    "cm^-1": "cm-1",
    "1/cm-1": "cm-1",
    "wavenumber": "cm-1",
    "wavenumbers": "cm-1",
    "wavenumbers (cm-1)": "cm-1",
}

# Micrometers → convert to nm (×1000); Spectrum only stores nm | cm-1.
_XUNIT_TO_NM_SCALE: dict[str, float] = {
    "micrometers": 1000.0,
    "micrometer": 1000.0,
    "microns": 1000.0,
    "micron": 1000.0,
    "um": 1000.0,
    "µm": 1000.0,
}

_YUNIT_ALIASES: dict[str, YUnit] = {
    "absorbance": "A",
    "a": "A",
    "au": "A",
    "abs": "A",
    "optical density": "A",
    "transmittance": "percent_T",
    "transmission": "percent_T",
    "%t": "percent_T",
    "% t": "percent_T",
    "%transmittance": "percent_T",
    "% transmittance": "percent_T",
    "percent transmittance": "percent_T",
    "percent_t": "percent_T",
    "arbitrary units": "intensity",
    "arbitrary unit": "intensity",
    "intensity": "intensity",
    "counts": "intensity",
    "signal": "intensity",
    "relative intensity": "intensity",
}

_JCAMP_SUFFIXES = {".jdx", ".dx", ".jcm"}


def _sniff_delimiter(line: str) -> str:
    if "\t" in line and line.count("\t") >= line.count(","):
        return "\t"
    if "," in line:
        return ","
    if ";" in line:
        return ";"
    return ","


def _parse_csv_xy(
    path: Path,
    x_col: int | str,
    y_col: int | str,
    *,
    delimiter: str | None,
    skip_header: int | None,
) -> tuple[np.ndarray, np.ndarray]:
    """Read two numeric columns, honoring # comments and an optional header row."""
    raw_lines: list[str] = []
    with path.open(newline="") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped or stripped.lstrip().startswith("#"):
                continue
            raw_lines.append(stripped)

    if not raw_lines:
        raise ValueError(f"empty or comment-only CSV: {path}")

    delim = delimiter or _sniff_delimiter(raw_lines[0])
    first_fields = [c.strip() for c in raw_lines[0].split(delim)]

    def _looks_numeric(fields: list[str]) -> bool:
        try:
            float(fields[0].replace(",", ""))  # single-field sanity; real parse below
            # Prefer: all fields that we care about parse as float
            for f in fields:
                float(f)
            return True
        except ValueError:
            return False

    # Decide whether first non-comment line is a header.
    has_header = False
    if isinstance(x_col, str) or isinstance(y_col, str):
        has_header = True
    elif skip_header is not None:
        has_header = skip_header > 0
    else:
        has_header = not _looks_numeric(first_fields)

    data_lines = raw_lines
    header: list[str] | None = None
    if has_header:
        header = first_fields
        # If skip_header is an int > 1, skip that many leading data rows after header.
        n_skip = 1 if skip_header is None else max(1, skip_header)
        data_lines = raw_lines[n_skip:]
    elif skip_header:
        data_lines = raw_lines[skip_header:]

    if header is not None:
        try:
            xi = header.index(str(x_col)) if isinstance(x_col, str) else int(x_col)
            yi = header.index(str(y_col)) if isinstance(y_col, str) else int(y_col)
        except ValueError as exc:
            raise ValueError(
                f"column not in header {header}: x_col={x_col!r}, y_col={y_col!r}"
            ) from exc
    else:
        xi = int(x_col)
        yi = int(y_col)

    xs: list[float] = []
    ys: list[float] = []
    for i, line in enumerate(data_lines):
        fields = [c.strip() for c in line.split(delim)]
        try:
            xs.append(float(fields[xi]))
            ys.append(float(fields[yi]))
        except (ValueError, IndexError) as exc:
            raise ValueError(
                f"could not parse numeric x/y at data row {i} in {path}: {line!r}"
            ) from exc

    if not xs:
        raise ValueError(f"no numeric rows in {path}")
    return np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)


def ingest_csv(
    path: str | Path,
    x_col: int | str = 0,
    y_col: int | str = 1,
    *,
    x_unit: XUnit = "nm",
    y_unit: YUnit = "intensity",
    title: str | None = None,
    delimiter: str | None = None,
    skip_header: int | None = None,
    meta: dict[str, Any] | None = None,
) -> Spectrum:
    """Load a spectrum from a CSV/TSV-like file.

    Parameters
    ----------
    path :
        Path to the file.
    x_col, y_col :
        Column index (int) or header name (str).
    x_unit, y_unit :
        Axis unit tags stored on the Spectrum.
    title :
        Display title; defaults to the file stem.
    delimiter :
        Field delimiter; None sniffs from the first data/header line.
    skip_header :
        If using a header row, number of leading non-comment lines to skip
        (default 1 = the header). If columns are ints and the first line is
        numeric, defaults to 0.
    meta :
        Extra metadata dict attached to the Spectrum.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)

    x, y = _parse_csv_xy(
        path, x_col, y_col, delimiter=delimiter, skip_header=skip_header
    )
    return Spectrum(
        x=x,
        y=y,
        x_unit=x_unit,
        y_unit=y_unit,
        title=title if title is not None else path.stem,
        meta={"source": str(path), **(meta or {})},
    )


def is_jcamp_path(path: str | Path) -> bool:
    """True when the path suffix looks like JCAMP-DX (``.jdx`` / ``.dx`` / ``.jcm``)."""
    return Path(path).suffix.lower() in _JCAMP_SUFFIXES


def _normalize_unit_key(raw: Any) -> str:
    if raw is None:
        return ""
    return str(raw).strip().lower().replace("_", " ")


def _map_jcamp_x_unit(
    xunits_raw: Any, data_type: Any
) -> tuple[XUnit, float, str | None]:
    """Return (x_unit, x_scale, note).

    ``x_scale`` multiplies the abscissa (e.g. µm → nm).
    """
    key = _normalize_unit_key(xunits_raw)
    note: str | None = None

    if key in _XUNIT_ALIASES:
        return _XUNIT_ALIASES[key], 1.0, None
    if key in _XUNIT_TO_NM_SCALE:
        scale = _XUNIT_TO_NM_SCALE[key]
        return "nm", scale, f"converted x from {xunits_raw!r} to nm (×{scale:g})"

    # Hint from ##DATA TYPE when ##XUNITS missing/unknown.
    dt = _normalize_unit_key(data_type)
    if not key:
        if "uv" in dt or "vis" in dt:
            return "nm", 1.0, "x_unit inferred as nm from DATA TYPE (XUNITS missing)"
        if "infrared" in dt or "ir " in dt or dt == "ir" or "raman" in dt:
            return (
                "cm-1",
                1.0,
                "x_unit inferred as cm-1 from DATA TYPE (XUNITS missing)",
            )

    raise ValueError(
        f"unsupported JCAMP XUNITS={xunits_raw!r} "
        f"(mapped Spectrum.x_unit must be 'nm' or 'cm-1'; "
        f"DATA TYPE={data_type!r}). "
        "Known: NANOMETERS/NM, 1/CM/CM-1, MICROMETERS (converted to nm)."
    )


def _map_jcamp_y_unit(yunits_raw: Any) -> tuple[YUnit, str | None]:
    """Return (y_unit, note). Unknown → intensity with a documentation note."""
    key = _normalize_unit_key(yunits_raw)
    if key in _YUNIT_ALIASES:
        return _YUNIT_ALIASES[key], None
    if not key:
        return "intensity", "y_unit defaulted to intensity (YUNITS missing)"
    return (
        "intensity",
        f"unknown JCAMP YUNITS={yunits_raw!r}; stored as intensity (no conversion)",
    )


def _maybe_scale_transmittance(y: np.ndarray, yunits_raw: Any, y_unit: YUnit) -> tuple[np.ndarray, str | None]:
    """If YUNITS is fraction transmittance (max ≲ 1.5), scale to percent_T."""
    if y_unit != "percent_T":
        return y, None
    key = _normalize_unit_key(yunits_raw)
    # Explicit percent labels → leave as-is.
    if "%" in key or "percent" in key:
        return y, None
    finite = y[np.isfinite(y)]
    if finite.size == 0:
        return y, None
    ymax = float(np.nanmax(finite))
    if ymax <= 1.5:
        return y * 100.0, (
            f"scaled YUNITS={yunits_raw!r} from fraction to percent_T (×100)"
        )
    return y, None


def ingest_jcamp(
    path: str | Path,
    *,
    title: str | None = None,
    meta: dict[str, Any] | None = None,
) -> Spectrum:
    """Load a spectrum from a JCAMP-DX file (``.jdx`` / ``.dx``).

    Uses the MIT-licensed ``jcamp`` package (``jcamp.readfile`` → dict with
    ``x`` / ``y`` arrays plus header fields).

    Unit mapping (basic)
    --------------------
    XUNITS
        ``NANOMETERS`` / ``NM`` → ``nm``;
        ``1/CM`` / ``CM-1`` → ``cm-1``;
        ``MICROMETERS`` / ``UM`` → convert ×1000 → ``nm``;
        missing XUNITS may be inferred from ``DATA TYPE`` (UV/VIS→nm, IR→cm-1);
        other x units raise ``ValueError`` (documented unknowns).
    YUNITS
        ``ABSORBANCE`` → ``A``;
        ``TRANSMITTANCE`` / ``%T`` / percent labels → ``percent_T``
        (fraction transmittance with max ≤ 1.5 is scaled ×100);
        unknown / missing → ``intensity`` with a note in ``meta["unit_notes"]``.

    Original JCAMP ``xunits`` / ``yunits`` / ``data type`` / ``title`` are kept
    in ``Spectrum.meta``. This does **not** identify compounds.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)

    try:
        import jcamp
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "JCAMP ingest requires the 'jcamp' package (MIT). "
            "Install with: pip install jcamp"
        ) from exc

    try:
        raw = jcamp.readfile(str(path))
    except Exception as exc:  # noqa: BLE001 — surface parse failures clearly
        raise ValueError(f"JCAMP-DX parse failed for {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError(f"JCAMP-DX parse returned unexpected type: {type(raw)!r}")

    if "x" not in raw or "y" not in raw:
        raise ValueError(
            f"JCAMP-DX file has no x/y data arrays: {path} "
            f"(keys={sorted(raw.keys())})"
        )

    x = np.asarray(raw["x"], dtype=float)
    y = np.asarray(raw["y"], dtype=float)
    if x.size == 0 or y.size == 0:
        raise ValueError(f"JCAMP-DX file has empty x/y arrays: {path}")
    if x.shape != y.shape:
        raise ValueError(
            f"JCAMP-DX x/y length mismatch in {path}: {x.shape} vs {y.shape}"
        )

    xunits_raw = raw.get("xunits")
    yunits_raw = raw.get("yunits")
    data_type = raw.get("data type")

    x_unit, x_scale, x_note = _map_jcamp_x_unit(xunits_raw, data_type)
    y_unit, y_note = _map_jcamp_y_unit(yunits_raw)
    if x_scale != 1.0:
        x = x * x_scale
    y, t_note = _maybe_scale_transmittance(y, yunits_raw, y_unit)

    unit_notes = [n for n in (x_note, y_note, t_note) if n]
    jcamp_meta = {
        "source": str(path),
        "format": "JCAMP-DX",
        "jcamp_xunits": xunits_raw,
        "jcamp_yunits": yunits_raw,
        "jcamp_data_type": data_type,
        "jcamp_title": raw.get("title"),
    }
    if unit_notes:
        jcamp_meta["unit_notes"] = unit_notes
    if meta:
        jcamp_meta.update(meta)

    display_title = title
    if display_title is None:
        jt = raw.get("title")
        display_title = str(jt).strip() if jt else path.stem

    return Spectrum(
        x=x,
        y=y,
        x_unit=x_unit,
        y_unit=y_unit,
        title=display_title,
        meta=jcamp_meta,
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
) -> Spectrum:
    """Dispatch ingest by file suffix (``.jdx``/``.dx`` → JCAMP; else CSV).

    CSV kwargs (``delimiter``, ``skip_header``, column/unit args) apply only to
    the CSV path. JCAMP units come from file headers.
    """
    path = Path(path)
    if is_jcamp_path(path):
        return ingest_jcamp(path, title=title, meta=meta)
    return ingest_csv(
        path,
        x_col=x_col,
        y_col=y_col,
        x_unit=x_unit,
        y_unit=y_unit,
        title=title,
        meta=meta,
        **csv_kwargs,
    )
