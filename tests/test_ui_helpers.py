"""Tests for UI helpers (no NiceGUI required)."""

from pathlib import Path

from chemspec.ui_helpers import (
    FIXTURE_PRESETS,
    axis_label,
    format_provenance,
    guess_column_mapping,
    peak_export_filename,
    provenance_from_state,
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


def test_guess_uvvis_short_a_column_is_absorbance() -> None:
    """Column named A/AU/Abs/OD must map to y_unit=A (A↔%T), not intensity."""
    for yname in ("A", "AU", "Abs", "OD", "abs", "au"):
        g = guess_column_mapping(["wavelength_nm", yname])
        assert g["y_col"] == yname, yname
        assert g["y_unit"] == "A", yname


def test_guess_absolute_intensity_not_absorbance() -> None:
    """Bare 'abs' substring must not mis-tag absolute_intensity as absorbance."""
    g = guess_column_mapping(["wavelength_nm", "absolute_intensity"])
    assert g["y_col"] == "absolute_intensity"
    assert g["y_unit"] == "intensity"


def test_guess_ir_mapping() -> None:
    g = guess_column_mapping(["wavenumber_cm-1", "intensity"])
    assert g["x_col"] == "wavenumber_cm-1"
    assert g["y_col"] == "intensity"
    assert g["x_unit"] == "cm-1"
    assert g["y_unit"] == "intensity"


def test_guess_ir_stays_intensity_unless_percent_t() -> None:
    g = guess_column_mapping(["wavenumber_cm-1", "intensity"])
    assert g["y_unit"] == "intensity"
    g_t = guess_column_mapping(["wavenumber_cm-1", "transmittance"])
    assert g_t["y_unit"] == "percent_T"


def test_guess_empty_falls_back_to_indices() -> None:
    g = guess_column_mapping([])
    assert g["x_col"] == 0
    assert g["y_col"] == 1


def test_fixture_presets_exist() -> None:
    for key, cfg in FIXTURE_PRESETS.items():
        assert cfg["path"].is_file(), key


def test_uvvis_fixture_preset_is_absorbance() -> None:
    cfg = FIXTURE_PRESETS["uvvis"]
    assert cfg["y_unit"] == "A"
    assert cfg["y_col"] == "absorbance"
    g = guess_column_mapping(sniff_csv_header(cfg["path"]))
    assert g["y_unit"] == "A"


def test_ir_fixture_preset_is_intensity() -> None:
    cfg = FIXTURE_PRESETS["ir"]
    assert cfg["y_unit"] == "intensity"
    g = guess_column_mapping(sniff_csv_header(cfg["path"]))
    assert g["y_unit"] == "intensity"


def test_axis_labels() -> None:
    assert axis_label("nm", "A") == ("Wavelength (nm)", "Absorbance")
    assert "cm" in axis_label("cm-1", "intensity")[0]


def test_waterfall_fixture_dir_exists() -> None:
    from chemspec.ui_helpers import WATERFALL_FIXTURE_DIR

    assert WATERFALL_FIXTURE_DIR.is_dir()
    csvs = list(WATERFALL_FIXTURE_DIR.glob("*.csv"))
    assert len(csvs) >= 3


def test_peak_export_filename() -> None:
    assert peak_export_filename("uvvis synthetic") == "uvvis_synthetic_peaks.csv"
    assert peak_export_filename(None) == "peaks.csv"
    assert peak_export_filename("") == "peaks.csv"


def test_format_provenance_basic() -> None:
    s = format_provenance(
        source="/data/fixtures/uvvis_synthetic.csv",
        x_unit="nm",
        y_unit="A",
        baseline_method=None,
        peak_count=2,
        package_version="0.1.0",
    )
    assert "source=uvvis_synthetic.csv" in s
    assert "x=nm" in s
    assert "y=A" in s
    assert "baseline=none" in s
    assert "peaks=2" in s
    assert "v=0.1.0" in s


def test_format_provenance_active_baseline() -> None:
    s = format_provenance(
        source="ir_synthetic.csv",
        x_unit="cm-1",
        y_unit="intensity",
        baseline_method="polynomial",
        peak_count=3,
    )
    assert "baseline=polynomial" in s
    assert "y=intensity" in s
    assert "v=" not in s


def test_provenance_from_state_respects_baseline_flag() -> None:
    on = provenance_from_state(
        primary_path="a.csv",
        spectrum_title="t",
        x_unit="nm",
        y_unit="A",
        baseline_on=True,
        baseline_method="asls",
        peak_count=1,
        package_version="0.1.0",
    )
    off = provenance_from_state(
        primary_path="a.csv",
        spectrum_title="t",
        x_unit="nm",
        y_unit="A",
        baseline_on=False,
        baseline_method="asls",
        peak_count=1,
    )
    assert "baseline=asls" in on
    assert "baseline=none" in off
