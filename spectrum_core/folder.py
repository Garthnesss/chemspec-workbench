"""Load a folder of CSV / JCAMP / SPC spectra for overlay or waterfall / stack."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from spectrum_core.ingest import ingest, is_jcamp_path
from spectrum_core.overlay import stack
from spectrum_core.spectrum import Spectrum, XUnit, YUnit

_SPECTRUM_SUFFIXES = {".csv", ".tsv", ".txt", ".jdx", ".dx", ".jcm", ".spc"}


def list_spectrum_files(
    folder: str | Path,
    *,
    recursive: bool = False,
) -> list[Path]:
    """Return sorted spectrum file paths under ``folder``.

    Recognized suffixes: ``.csv``, ``.tsv``, ``.txt``, ``.jdx``, ``.dx``,
    ``.spc``, ``.jcm``. Hidden files (name starting with ``.``) are skipped.
    Sort is by lowercase file name (stable for ``t00``, ``t01``, …).
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(folder)
    if recursive:
        paths = [p for p in folder.rglob("*") if p.is_file()]
    else:
        paths = [p for p in folder.iterdir() if p.is_file()]
    out = [
        p
        for p in paths
        if p.suffix.lower() in _SPECTRUM_SUFFIXES and not p.name.startswith(".")
    ]
    out.sort(key=lambda p: p.name.lower())
    return out


def ingest_folder(
    folder: str | Path,
    *,
    recursive: bool = False,
    x_col: int | str = 0,
    y_col: int | str = 1,
    x_unit: XUnit = "nm",
    y_unit: YUnit = "intensity",
    sort_by: Literal["name", "mtime"] = "name",
    require_matching_x_unit: bool = True,
) -> list[Spectrum]:
    """Ingest all spectrum files in ``folder`` (CSV / JCAMP / SPC).

    CSV files use the given column/unit args; JCAMP/SPC units come from headers.
    Order: ``name`` (default, case-insensitive) or ``mtime`` (oldest first).

    When ``require_matching_x_unit`` is True (default), every spectrum must
    share the first file's ``x_unit`` or ``ValueError`` is raised — same
    rule as ``overlay`` / ``stack``.
    """
    paths = list_spectrum_files(folder, recursive=recursive)
    if sort_by == "mtime":
        paths.sort(key=lambda p: p.stat().st_mtime)
    elif sort_by != "name":
        raise ValueError(f"sort_by must be 'name' or 'mtime', got {sort_by!r}")
    if sort_by == "name":
        paths.sort(key=lambda p: p.name.lower())

    if not paths:
        return []

    spectra: list[Spectrum] = []
    for path in paths:
        if is_jcamp_path(path):
            spec = ingest(path)
        else:
            spec = ingest(
                path,
                x_col=x_col,
                y_col=y_col,
                x_unit=x_unit,
                y_unit=y_unit,
            )
        spectra.append(spec)

    if require_matching_x_unit and spectra:
        x0 = spectra[0].x_unit
        for i, s in enumerate(spectra):
            if s.x_unit != x0:
                raise ValueError(
                    f"folder spectrum[{i}] ({s.title!r}) x_unit={s.x_unit!r} "
                    f"!= {x0!r}; waterfall/stack requires matching x units"
                )
    return spectra


def folder_waterfall(
    folder: str | Path,
    *,
    offset: float | None = None,
    **ingest_kwargs: Any,
) -> list[Spectrum]:
    """Ingest a folder and return ``stack(...)`` traces for waterfall display.

    Thin wrapper: ``stack(ingest_folder(...), offset=offset)``.
    """
    spectra = ingest_folder(folder, **ingest_kwargs)
    return stack(spectra, offset=offset)
