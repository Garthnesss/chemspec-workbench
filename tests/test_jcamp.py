"""JCAMP-DX ingest (offline fixtures; MIT jcamp package)."""

from pathlib import Path

import pytest

from spectrum_core import ingest, ingest_csv, ingest_jcamp, is_jcamp_path


def test_is_jcamp_path() -> None:
    assert is_jcamp_path("a.jdx")
    assert is_jcamp_path("a.DX")
    assert is_jcamp_path(Path("b.dx"))
    assert not is_jcamp_path("a.csv")


def test_ingest_jcamp_uvvis_fixture(uvvis_jdx: Path) -> None:
    spec = ingest_jcamp(uvvis_jdx)
    assert len(spec) == 101
    assert spec.x_unit == "nm"
    assert spec.y_unit == "A"
    assert spec.x.min() == pytest.approx(250.0)
    assert spec.x.max() == pytest.approx(450.0)
    assert spec.y.max() > 0.5
    assert spec.meta.get("format") == "JCAMP-DX"
    assert spec.meta.get("jcamp_xunits") == "NANOMETERS"
    assert "uvvis" in spec.title.lower() or spec.title


def test_ingest_jcamp_ir_fixture(ir_dx: Path) -> None:
    spec = ingest_jcamp(ir_dx)
    assert len(spec) == 81
    assert spec.x_unit == "cm-1"
    assert spec.y_unit == "percent_T"
    # Fixture stores transmittance as fraction → scaled to percent.
    assert spec.y.max() > 50
    assert "scaled" in " ".join(spec.meta.get("unit_notes", [])).lower()
    assert 800 <= spec.x.min() <= 900
    assert 3900 <= spec.x.max() <= 4100


def test_ingest_dispatch_jcamp(uvvis_jdx: Path) -> None:
    spec = ingest(uvvis_jdx)
    assert spec.x_unit == "nm"
    assert len(spec) == 101


def test_ingest_dispatch_keeps_csv(uvvis_csv: Path) -> None:
    spec = ingest(
        uvvis_csv,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    assert spec.y_unit == "A"
    assert len(spec) > 100


def test_ingest_jcamp_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ingest_jcamp(tmp_path / "nope.jdx")


def test_ingest_jcamp_bad_content(tmp_path: Path) -> None:
    bad = tmp_path / "broken.jdx"
    bad.write_text("this is not jcamp\n", encoding="utf-8")
    with pytest.raises(ValueError, match="JCAMP-DX"):
        ingest_jcamp(bad)


def test_ingest_jcamp_unsupported_xunits(tmp_path: Path) -> None:
    text = """##TITLE=bad units
##JCAMP-DX=4.24
##DATA TYPE=NMR SPECTRUM
##XUNITS=HZ
##YUNITS=ARBITRARY UNITS
##XFACTOR=1.0
##YFACTOR=1.0
##FIRSTX=0.0
##LASTX=4.0
##NPOINTS=5
##FIRSTY=0.0
##XYDATA=(X++(Y..Y))
0.0 0.0 0.1 0.2 0.1 0.0
##END=
"""
    path = tmp_path / "nmr_hz.jdx"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported JCAMP XUNITS"):
        ingest_jcamp(path)


def test_ingest_jcamp_micrometer_to_nm(tmp_path: Path) -> None:
    text = """##TITLE=um to nm
##JCAMP-DX=4.24
##DATA TYPE=UV/VIS SPECTRUM
##XUNITS=MICROMETERS
##YUNITS=ABSORBANCE
##XFACTOR=1.0
##YFACTOR=1.0
##FIRSTX=0.250
##LASTX=0.260
##NPOINTS=6
##FIRSTY=0.1
##XYDATA=(X++(Y..Y))
0.250 0.10 0.15 0.40 0.35 0.20 0.12
##END=
"""
    path = tmp_path / "um.jdx"
    path.write_text(text, encoding="utf-8")
    spec = ingest_jcamp(path)
    assert spec.x_unit == "nm"
    assert spec.x[0] == pytest.approx(250.0)
    assert any("converted" in n.lower() for n in spec.meta.get("unit_notes", []))


def test_csv_still_works_alongside_jcamp(uvvis_csv: Path) -> None:
    """Regression: CSV path unchanged."""
    spec = ingest_csv(
        uvvis_csv,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    assert len(spec) > 100
