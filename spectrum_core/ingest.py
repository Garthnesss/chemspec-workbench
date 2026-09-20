"""CSV and JCAMP-DX ingest adapters.

Ingest policies (CSV + post-parse shared)
----------------------------------------
**X-direction**
    Native order is **preserved** (descending / reversed x is common for IR
    ``cm-1`` exports). Peak FWHM/area already tolerate either direction.
    Call :func:`ensure_ascending_x` when a consumer requires monotonic
    ascending ``x`` (documented API helper — not applied automatically).

**Duplicate x / uneven spacing**
    Retained as-is. No deduplication or resampling on ingest.

**Non-finite values (NaN / ±Inf)**
    Default ``skip_nonfinite=True``: rows with non-finite ``x`` **or** ``y``
    are skipped; skip counts are recorded in ``Spectrum.meta`` under
    ``ingest_skipped_nonfinite``. If every row is skipped (or the file is
    empty), a clear ``ValueError`` is raised. Set ``skip_nonfinite=False``
    to keep NaN/Inf in ``y`` (non-finite ``x`` is still skipped — unusable
    abscissa).

**CSV delimiters / quoting**
    Parsed with the stdlib ``csv`` module. Delimiter is sniffed
    (``,`` / ``;`` / tab) unless ``delimiter=`` is passed. Quoted fields
    (commas inside quotes) are handled correctly.

**Missing values / extra columns**
    Empty or blank ``x``/``y`` cells → row skipped (counted in
    ``ingest_skipped_missing``). Extra columns beyond the selected pair
    are ignored.

**%T vs absorbance headers**
    ``ingest_csv`` does **not** auto-override caller ``y_unit``. Use
    :func:`y_unit_from_header` (or UI ``guess_column_mapping``) to map
    header names such as ``%T`` / ``Absorbance`` → ``percent_T`` / ``A``.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Literal

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

_HEADER_TOKEN_RE = re.compile(r"[a-z0-9%]+", re.IGNORECASE)

XDirection = Literal["ascending", "descending", "unordered"]


def x_direction(x: np.ndarray) -> XDirection:
    """Classify abscissa order: ascending, descending, or unordered (ties OK)."""
    arr = np.asarray(x, dtype=float)
    if arr.size < 2:
        return "ascending"
    d = np.diff(arr)
    # Ignore exact zeros (duplicate x) when classifying monotonicity.
    nonzero = d[d != 0.0]
    if nonzero.size == 0:
        return "ascending"
    if np.all(nonzero > 0):
        return "ascending"
    if np.all(nonzero < 0):
        return "descending"
    return "unordered"


def ensure_ascending_x(spectrum: Spectrum) -> Spectrum:
    """Return a copy with ``x`` sorted ascending (``y`` follows).

    No-op copy when already ascending. Records ``meta["x_sorted"]=True`` and
    the original direction when a reorder occurs. Use when a downstream
    algorithm requires monotonic ascending ``x``; ingest itself does **not**
    auto-sort (preserves IR descending exports).
    """
    direction = x_direction(spectrum.x)
    if direction == "ascending":
        out = spectrum.copy()
        out.meta.setdefault("x_direction", direction)
        return out
    order = np.argsort(spectrum.x, kind="mergesort")  # stable
    out = Spectrum(
        x=spectrum.x[order],
        y=spectrum.y[order],
        x_unit=spectrum.x_unit,
        y_unit=spectrum.y_unit,
        title=spectrum.title,
        meta=dict(spectrum.meta),
    )
    out.meta["x_direction_original"] = direction
    out.meta["x_sorted"] = True
    out.meta["x_direction"] = "ascending"
    return out


def y_unit_from_header(name: str) -> YUnit | None:
    """Map a CSV header name to a Spectrum ``y_unit``, or ``None`` if unclear.

    Recognizes absorbance (``Absorbance``, ``A``, ``AU``, ``Abs``, ``OD``) and
    transmittance / ``%T`` labels. Does not guess ``intensity`` from vague
    names — callers keep their default.
    """
    low = name.strip().lower().replace("_", " ")
    if "absorbance" in low or "optical density" in low:
        return "A"
    if (
        "transmittance" in low
        or "transmission" in low
        or "%t" in low.replace(" ", "")
        or "percent t" in low
        or low in {"% t", "t%", "percent_t", "pct t", "pct_t"}
    ):
        return "percent_T"
    toks = {m.group(0).lower() for m in _HEADER_TOKEN_RE.finditer(name)}
    if toks & {"a", "abs", "au", "od"}:
        return "A"
    if toks & {"percent_t", "pct_t", "%t", "t%"}:
        return "percent_T"
    return None


def _sniff_delimiter(sample: str) -> str:
    """Pick ``,`` / ``;`` / tab from a small text sample."""
    # Prefer csv.Sniffer when it works; fall back to simple counts.
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        if dialect.delimiter in {",", ";", "\t"}:
            return dialect.delimiter
    except csv.Error:
        pass
    # Count on first non-empty line.
    line = next((ln for ln in sample.splitlines() if ln.strip()), "")
    if "\t" in line and line.count("\t") >= line.count(",") and line.count("\t") >= line.count(
        ";"
    ):
        return "\t"
    if line.count(";") > line.count(","):
        return ";"
    if "," in line:
        return ","
    if ";" in line:
        return ";"
    if "\t" in line:
        return "\t"
    return ","


def _looks_numeric_row(fields: list[str]) -> bool:
    if not fields:
        return False
    try:
        for f in fields:
            s = f.strip()
            if s == "":
                return False
            float(s)
        return True
    except ValueError:
        return False


def _parse_float_cell(raw: str) -> float | None:
    """Parse a cell; blank → None; NaN/Inf strings → float nan/inf."""
    s = raw.strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_csv_xy(
    path: Path,
    x_col: int | str,
    y_col: int | str,
    *,
    delimiter: str | None,
    skip_header: int | None,
    skip_nonfinite: bool,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Read two numeric columns via the ``csv`` module.

    Returns ``(x, y, stats)`` where stats include skip counts and delimiter.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    # Drop full-line # comments (and blank lines) before csv parsing so
    # fixture READMEs / unit hints do not confuse the sniffer.
    kept_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue
        kept_lines.append(line)
    if not kept_lines:
        raise ValueError(f"empty or comment-only CSV: {path}")

    sample = "\n".join(kept_lines[:40])
    delim = delimiter or _sniff_delimiter(sample)
    reader = csv.reader(kept_lines, delimiter=delim)
    rows = [list(r) for r in reader]
    if not rows:
        raise ValueError(f"empty or comment-only CSV: {path}")

    first_fields = [c.strip() for c in rows[0]]
    has_header = False
    if isinstance(x_col, str) or isinstance(y_col, str):
        has_header = True
    elif skip_header is not None:
        has_header = skip_header > 0
    else:
        has_header = not _looks_numeric_row(first_fields)

    header: list[str] | None = None
    data_rows = rows
    if has_header:
        header = first_fields
        n_skip = 1 if skip_header is None else max(1, skip_header)
        data_rows = rows[n_skip:]
    elif skip_header:
        data_rows = rows[skip_header:]

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
    skipped_missing = 0
    skipped_nonfinite = 0
    for i, fields in enumerate(data_rows):
        if xi >= len(fields) or yi >= len(fields):
            skipped_missing += 1
            continue
        xv = _parse_float_cell(fields[xi])
        yv = _parse_float_cell(fields[yi])
        if xv is None or yv is None:
            skipped_missing += 1
            continue
        x_ok = np.isfinite(xv)
        y_ok = np.isfinite(yv)
        if not x_ok:
            skipped_nonfinite += 1
            continue
        if not y_ok:
            if skip_nonfinite:
                skipped_nonfinite += 1
                continue
            # keep non-finite y when policy allows
        xs.append(xv)
        ys.append(yv)

    if not xs:
        raise ValueError(
            f"no numeric rows in {path} "
            f"(skipped_missing={skipped_missing}, "
            f"skipped_nonfinite={skipped_nonfinite})"
        )
    stats: dict[str, Any] = {
        "delimiter": delim,
        "ingest_skipped_missing": skipped_missing,
        "ingest_skipped_nonfinite": skipped_nonfinite,
        "skip_nonfinite": skip_nonfinite,
    }
    return np.asarray(xs, dtype=float), np.asarray(ys, dtype=float), stats


def _apply_array_policy(
    x: np.ndarray,
    y: np.ndarray,
    *,
    skip_nonfinite: bool,
    path: Path | None = None,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Shared finite-value filter for CSV/JCAMP arrays."""
    if x.shape != y.shape:
        where = f" in {path}" if path else ""
        raise ValueError(f"x/y length mismatch{where}: {x.shape} vs {y.shape}")
    skipped = 0
    if skip_nonfinite:
        mask = np.isfinite(x) & np.isfinite(y)
        skipped = int((~mask).sum())
        x, y = x[mask], y[mask]
    else:
        mask = np.isfinite(x)
        skipped = int((~mask).sum())
        x, y = x[mask], y[mask]
    if x.size == 0:
        where = f" in {path}" if path else ""
        raise ValueError(
            f"no finite data points{where} "
            f"(skipped_nonfinite={skipped}, skip_nonfinite={skip_nonfinite})"
        )
    return x, y, {"ingest_skipped_nonfinite": skipped, "skip_nonfinite": skip_nonfinite}


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
    skip_nonfinite: bool = True,
    meta: dict[str, Any] | None = None,
) -> Spectrum:
    """Load a spectrum from a CSV/TSV-like file (stdlib ``csv`` parser).

    Parameters
    ----------
    path :
        Path to the file.
    x_col, y_col :
        Column index (int) or header name (str).
    x_unit, y_unit :
        Axis unit tags stored on the Spectrum. Not inferred from headers
        unless the caller uses :func:`y_unit_from_header`.
    title :
        Display title; defaults to the file stem.
    delimiter :
        Field delimiter; None sniffs from the first data/header lines
        (``,`` / ``;`` / tab). Quoted fields are supported.
    skip_header :
        If using a header row, number of leading non-comment lines to skip
        (default 1 = the header). If columns are ints and the first line is
        numeric, defaults to 0.
    skip_nonfinite :
        When True (default), drop rows with NaN/Inf in ``x`` or ``y``.
        See module docstring.
    meta :
        Extra metadata dict attached to the Spectrum.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)

    x, y, stats = _parse_csv_xy(
        path,
        x_col,
        y_col,
        delimiter=delimiter,
        skip_header=skip_header,
        skip_nonfinite=skip_nonfinite,
    )
    merged = {"source": str(path), "x_direction": x_direction(x), **stats}
    if meta:
        merged.update(meta)
    return Spectrum(
        x=x,
        y=y,
        x_unit=x_unit,
        y_unit=y_unit,
        title=title if title is not None else path.stem,
        meta=merged,
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


def _maybe_scale_transmittance(
    y: np.ndarray, yunits_raw: Any, y_unit: YUnit
) -> tuple[np.ndarray, str | None]:
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
    skip_nonfinite: bool = True,
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

    X-direction is preserved (often descending for IR). Use
    :func:`ensure_ascending_x` if needed. Non-finite points follow the same
    ``skip_nonfinite`` policy as CSV.

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

    try:
        x, y, fin_stats = _apply_array_policy(
            x, y, skip_nonfinite=skip_nonfinite, path=path
        )
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    xunits_raw = raw.get("xunits")
    yunits_raw = raw.get("yunits")
    data_type = raw.get("data type")

    x_unit, x_scale, x_note = _map_jcamp_x_unit(xunits_raw, data_type)
    y_unit, y_note = _map_jcamp_y_unit(yunits_raw)
    if x_scale != 1.0:
        x = x * x_scale
    y, t_note = _maybe_scale_transmittance(y, yunits_raw, y_unit)

    unit_notes = [n for n in (x_note, y_note, t_note) if n]
    jcamp_meta: dict[str, Any] = {
        "source": str(path),
        "format": "JCAMP-DX",
        "jcamp_xunits": xunits_raw,
        "jcamp_yunits": yunits_raw,
        "jcamp_data_type": data_type,
        "jcamp_title": raw.get("title"),
        "x_direction": x_direction(x),
        **fin_stats,
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

    CSV kwargs (``delimiter``, ``skip_header``, ``skip_nonfinite``, column/unit
    args) apply only to the CSV path. JCAMP units come from file headers;
    ``skip_nonfinite`` is honored for JCAMP when passed.
    """
    path = Path(path)
    if is_jcamp_path(path):
        skip_nf = csv_kwargs.pop("skip_nonfinite", True)
        if csv_kwargs:
            # Ignore leftover CSV-only kwargs silently for dispatch convenience.
            pass
        return ingest_jcamp(
            path, title=title, meta=meta, skip_nonfinite=skip_nf
        )
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
