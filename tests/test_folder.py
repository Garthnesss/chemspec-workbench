"""Folder ingest + waterfall / stack."""

from pathlib import Path
import shutil

import pytest

from spectrum_core import (
    folder_waterfall,
    ingest_folder,
    list_spectrum_files,
    stack,
)


def test_list_waterfall_fixtures():
    root = Path(__file__).resolve().parents[1] / "fixtures" / "waterfall"
    paths = list_spectrum_files(root)
    names = [p.name for p in paths]
    assert names == [
        "t00_synthetic.csv",
        "t01_synthetic.csv",
        "t02_synthetic.csv",
    ]


def test_ingest_folder_uvvis_waterfall():
    root = Path(__file__).resolve().parents[1] / "fixtures" / "waterfall"
    spectra = ingest_folder(
        root,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    assert len(spectra) == 3
    assert all(s.x_unit == "nm" for s in spectra)
    assert all(s.y_unit == "A" for s in spectra)


def test_folder_waterfall_uses_stack_offsets():
    root = Path(__file__).resolve().parents[1] / "fixtures" / "waterfall"
    stacked = folder_waterfall(
        root,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
        offset=1.0,
    )
    assert len(stacked) == 3
    assert stacked[0].meta["stack_offset"] == 0.0
    assert stacked[1].meta["stack_offset"] == 1.0
    assert stacked[2].meta["stack_offset"] == 2.0
    raw = ingest_folder(
        root,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    via_stack = stack(raw, offset=1.0)
    for a, b in zip(stacked, via_stack):
        assert a.meta["stack_offset"] == b.meta["stack_offset"]


def test_ingest_folder_empty(tmp_path: Path):
    assert ingest_folder(tmp_path) == []


def test_list_spectrum_files_not_a_dir(tmp_path: Path):
    f = tmp_path / "nope.txt"
    f.write_text("x")
    with pytest.raises(NotADirectoryError):
        list_spectrum_files(f)


def test_ingest_folder_mismatched_x_unit_jcamp(tmp_path: Path):
    """JCAMP UV-Vis (nm) + IR (cm-1) in one folder must fail matching check."""
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    shutil.copy(fixtures / "uvvis_synthetic.jdx", tmp_path / "uvvis_synthetic.jdx")
    shutil.copy(fixtures / "ir_synthetic.dx", tmp_path / "ir_synthetic.dx")
    with pytest.raises(ValueError, match="x_unit"):
        ingest_folder(tmp_path, require_matching_x_unit=True)
