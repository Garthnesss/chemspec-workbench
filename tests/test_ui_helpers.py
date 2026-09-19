"""Tests for UI helpers (no NiceGUI required)."""

from pathlib import Path

from chemspec.ui_helpers import (
    FIXTURE_PRESETS,
    axis_label,
    guess_column_mapping,
    sniff_csv_header,
)


def test_sniff_uvvis_headers(uvvis_csv: Path) -> None:
    headers = sniff_csv_header(uvvis_csv)
    assert headers == ["wavelength_nm", "absorbance"]


def test_sniff_ir_headers(ir_csv: Path) -> None:
    headers = sniff_csv_header(ir_csv)
    assert headers == ["wavenumber_cm-1", "intensity"]


def test_guess_uvvis_mapping() -> None:
    g = guess_column_mapping(["wavelength_nm", "absorbance"])
    assert g["x_col"] == "wavelength_nm"
    assert g["y_col"] == "absorbance"
    assert g["x_unit"] == "nm"
    assert g["y_unit"] == "A"


def test_guess_ir_mapping() -> None:
    g = guess_column_mapping(["wavenumber_cm-1", "intensity"])
    assert g["x_col"] == "wavenumber_cm-1"
    assert g["y_col"] == "intensity"
    assert g["x_unit"] == "cm-1"
    assert g["y_unit"] == "intensity"


def test_guess_empty_falls_back_to_indices() -> None:
    g = guess_column_mapping([])
    assert g["x_col"] == 0
    assert g["y_col"] == 1


def test_fixture_presets_exist() -> None:
    for key, cfg in FIXTURE_PRESETS.items():
        assert cfg["path"].is_file(), key


def test_axis_labels() -> None:
    assert axis_label("nm", "A") == ("Wavelength (nm)", "Absorbance")
    assert "cm" in axis_label("cm-1", "intensity")[0]
