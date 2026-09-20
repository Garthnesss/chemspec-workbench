"""Peak table CSV export."""

from pathlib import Path

from spectrum_core import Peak, find_peaks, ingest_csv, peaks_to_csv
from spectrum_core.export_peaks import PEAK_CSV_FIELDS


def test_peaks_to_csv_string_and_header():
    peaks = [
        Peak(index=10, x=280.0, y=0.9, prominence=0.5, fwhm=12.0, area=8.5),
        Peak(index=20, x=350.0, y=0.6, prominence=0.3, fwhm=15.0, area=6.0),
    ]
    text = peaks_to_csv(peaks)
    lines = text.strip().split("\n")
    assert lines[0] == ",".join(PEAK_CSV_FIELDS)
    assert PEAK_CSV_FIELDS[:6] == ("index", "x", "y", "prominence", "fwhm", "area")
    assert "width_definition" in PEAK_CSV_FIELDS
    assert "left_boundary_x" in PEAK_CSV_FIELDS
    assert "prominence_relative_half_height" in text
    assert "280.0" in lines[1]
    assert "12.0" in lines[1]
    assert "350.0" in lines[2]


def test_peaks_to_csv_empty():
    text = peaks_to_csv([])
    assert text.strip() == ",".join(PEAK_CSV_FIELDS)


def test_peaks_to_csv_includes_contract_fields_for_real_peak(uvvis_csv: Path):
    spec = ingest_csv(
        uvvis_csv,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    peaks = find_peaks(spec, prominence=0.15)
    text = peaks_to_csv(peaks)
    header = text.split("\n")[0]
    for col in (
        "width_definition",
        "half_max_level",
        "left_boundary_x",
        "right_boundary_x",
        "area_definition",
        "baseline_reference_note",
    ):
        assert col in header
    assert "prominence_relative_half_height" in text


def test_peaks_to_csv_writes_file(tmp_path: Path, uvvis_csv: Path):
    spec = ingest_csv(
        uvvis_csv,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    peaks = find_peaks(spec, prominence=0.15)
    out = tmp_path / "peaks.csv"
    text = peaks_to_csv(peaks, out)
    assert out.is_file()
    assert out.read_text(encoding="utf-8") == text
    assert text.startswith("index,x,y,prominence,fwhm,area,")
    assert "width_definition" in text.split("\n")[0]
    # Real peaks from the fixture should carry finite FWHM/area columns.
    assert peaks and peaks[0].fwhm == peaks[0].fwhm
