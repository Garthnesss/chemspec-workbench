"""CSV (and stub) ingest adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from spectrum_core.spectrum import Spectrum, XUnit, YUnit


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


def ingest_jcamp_stub(path: str | Path) -> Spectrum:
    """JCAMP-DX ingest is not implemented in Phase 0 (stub)."""
    raise NotImplementedError(
        "JCAMP-DX ingest is Planned, not Implemented. Use ingest_csv for Phase 0."
    )
