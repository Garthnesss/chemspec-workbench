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


def test_folder_waterfall_empty_returns_empty(tmp_path: Path):
    assert folder_waterfall(tmp_path) == []


def test_ingest_folder_sort_by_mtime(tmp_path: Path):
    """mtime order (oldest first) can differ from name order."""
    fixtures = Path(__file__).resolve().parents[1] / "fixtures" / "waterfall"
    # Copy with deliberate mtime: z_first older name but newer mtime than a_second
    import os
    import time

    a = tmp_path / "z_late_name.csv"
    b = tmp_path / "a_early_name.csv"
    a.write_text((fixtures / "t00_synthetic.csv").read_text())
    time.sleep(0.05)
    b.write_text((fixtures / "t01_synthetic.csv").read_text())
    # Ensure a is older than b despite z_ vs a_ names
    now = time.time()
    os.utime(a, (now - 10, now - 10))
    os.utime(b, (now - 1, now - 1))

    by_name = ingest_folder(
        tmp_path,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
        sort_by="name",
    )
    by_mtime = ingest_folder(
        tmp_path,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
        sort_by="mtime",
    )
    assert [Path(s.meta["source"]).name for s in by_name] == [
        "a_early_name.csv",
        "z_late_name.csv",
    ]
    assert [Path(s.meta["source"]).name for s in by_mtime] == [
        "z_late_name.csv",
        "a_early_name.csv",
    ]


def test_ingest_folder_invalid_sort_by(tmp_path: Path):
    (tmp_path / "x.csv").write_text("wavelength_nm,absorbance\n1,0.1\n")
    with pytest.raises(ValueError, match="sort_by"):
        ingest_folder(tmp_path, sort_by="size")  # type: ignore[arg-type]


def test_list_spectrum_files_skips_hidden_and_non_spectrum(tmp_path: Path):
    (tmp_path / "keep.csv").write_text("x,y\n1,2\n")
    (tmp_path / ".hidden.csv").write_text("x,y\n1,2\n")
    (tmp_path / "notes.md").write_text("# not a spectrum\n")
    (tmp_path / "data.npy").write_bytes(b"nope")
    paths = list_spectrum_files(tmp_path)
    assert [p.name for p in paths] == ["keep.csv"]


def test_list_spectrum_files_recursive(tmp_path: Path):
    sub = tmp_path / "nested"
    sub.mkdir()
    (tmp_path / "top.csv").write_text("x,y\n1,2\n")
    (sub / "deep.jdx").write_text("##TITLE=nested\n##END=\n")
    flat = list_spectrum_files(tmp_path, recursive=False)
    deep = list_spectrum_files(tmp_path, recursive=True)
    assert [p.name for p in flat] == ["top.csv"]
    assert sorted(p.name for p in deep) == ["deep.jdx", "top.csv"]


def test_folder_waterfall_auto_offset_from_fixture():
    """Default offset (None) still produces increasing stack_offset values."""
    root = Path(__file__).resolve().parents[1] / "fixtures" / "waterfall"
    stacked = folder_waterfall(
        root,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
        offset=None,
    )
    assert len(stacked) == 3
    assert stacked[0].meta["stack_offset"] == 0.0
    assert stacked[1].meta["stack_offset"] > 0
    assert stacked[2].meta["stack_offset"] == pytest.approx(
        2 * stacked[1].meta["stack_offset"]
    )
