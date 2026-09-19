"""CSV ingest loads fixtures."""

from spectrum_core import ingest_csv


def test_ingest_uvvis_by_name(uvvis_csv):
    spec = ingest_csv(
        uvvis_csv,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    assert len(spec) > 100
    assert spec.x_unit == "nm"
    assert spec.y_unit == "A"
    assert spec.x.min() < 250
    assert spec.x.max() > 400
    assert "uvvis" in spec.title.lower() or spec.title


def test_ingest_ir_by_index(ir_csv):
    # header + comments: use column names (safer) — also test names path
    spec = ingest_csv(
        ir_csv,
        x_col="wavenumber_cm-1",
        y_col="intensity",
        x_unit="cm-1",
        y_unit="intensity",
    )
    assert len(spec) > 100
    assert spec.x_unit == "cm-1"
    assert 1600 < spec.x.mean() < 3000


def test_ingest_missing_file(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        ingest_csv(tmp_path / "nope.csv")
