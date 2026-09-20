"""Round-trip and schema tests for ChemSpec session save/load."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from spectrum_core import (
    SESSION_FORMAT_VERSION,
    Peak,
    SessionError,
    Spectrum,
    find_peaks,
    ingest_csv,
    load_session,
    save_session,
    session_from_dict,
    session_to_dict,
)
from spectrum_core.session import (
    DEFAULT_PROCESSING,
    build_provenance,
    normalize_processing,
    session_download_filename,
    validate_session_dict,
)


def test_save_load_round_trip(tmp_path: Path, uvvis_csv: Path) -> None:
    spec = ingest_csv(
        uvvis_csv,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    peaks = find_peaks(spec, prominence=0.15)
    assert peaks, "fixture should yield peaks"
    processing = {
        "baseline_on": True,
        "baseline_method": "polynomial",
        "baseline_degree": 2,
        "flip_y_unit": True,
        "prominence": 0.15,
        "use_auto_prominence": False,
    }
    notes = "UV-Vis synthetic demo notes"
    path = tmp_path / "demo.csw.json"
    payload = save_session(
        path,
        spec,
        processing=processing,
        peaks=peaks,
        notes=notes,
        source_path=str(uvvis_csv),
    )
    assert path.is_file()
    assert payload["format_version"] == SESSION_FORMAT_VERSION
    assert "software_version" in payload
    assert payload["notes"] == notes
    assert payload["spectrum"]["source_path"] == str(uvvis_csv)
    assert len(payload["spectrum"]["x"]) == len(spec)
    assert len(payload["peaks"]) == len(peaks)

    loaded = load_session(path)
    assert loaded.format_version == SESSION_FORMAT_VERSION
    assert loaded.notes == notes
    assert loaded.source_path == str(uvvis_csv)
    assert loaded.processing["baseline_on"] is True
    assert loaded.processing["baseline_method"] == "polynomial"
    assert loaded.processing["baseline_degree"] == 2
    assert loaded.processing["flip_y_unit"] is True
    assert loaded.spectrum.x_unit == spec.x_unit
    assert loaded.spectrum.y_unit == spec.y_unit
    assert loaded.spectrum.title == spec.title
    np.testing.assert_allclose(loaded.spectrum.x, spec.x)
    np.testing.assert_allclose(loaded.spectrum.y, spec.y)
    assert len(loaded.peaks) == len(peaks)
    for a, b in zip(loaded.peaks, peaks, strict=True):
        assert a.index == b.index
        assert a.x == pytest.approx(b.x)
        assert a.y == pytest.approx(b.y)
        assert a.prominence == pytest.approx(b.prominence)
        if math.isfinite(b.fwhm):
            assert a.fwhm == pytest.approx(b.fwhm)
        else:
            assert math.isnan(a.fwhm)
        if math.isfinite(b.area):
            assert a.area == pytest.approx(b.area)
        else:
            assert math.isnan(a.area)
    assert "summary" in loaded.provenance
    assert loaded.provenance["peak_count"] == len(peaks)


def test_session_embeds_arrays_not_path_dependent(tmp_path: Path) -> None:
    """Reload works even when original path is gone / moved."""
    spec = Spectrum(
        x=np.array([400.0, 450.0, 500.0]),
        y=np.array([0.1, 0.8, 0.2]),
        x_unit="nm",
        y_unit="A",
        title="tiny",
        meta={"source": "/old/moved/path.csv", "label": "synthetic"},
    )
    gone = "/old/moved/path.csv"
    path = tmp_path / "embedded.chemspec.json"
    save_session(path, spec, source_path=gone, notes="")
    # Simulate path move: do not create the original file
    loaded = load_session(path)
    np.testing.assert_allclose(loaded.spectrum.x, spec.x)
    np.testing.assert_allclose(loaded.spectrum.y, spec.y)
    assert loaded.source_path == gone
    assert loaded.spectrum.meta.get("label") == "synthetic"


def test_session_nan_peak_fields_round_trip(tmp_path: Path) -> None:
    spec = Spectrum(
        x=np.linspace(0, 10, 11),
        y=np.ones(11),
        x_unit="nm",
        y_unit="intensity",
        title="flat",
    )
    peaks = [
        Peak(index=5, x=5.0, y=1.0, prominence=0.0, fwhm=float("nan"), area=float("nan"))
    ]
    path = tmp_path / "nan_peaks.csw.json"
    save_session(path, spec, peaks=peaks)
    # ensure JSON has nulls not NaN literals
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["peaks"][0]["fwhm"] is None
    assert raw["peaks"][0]["area"] is None
    loaded = load_session(path)
    assert math.isnan(loaded.peaks[0].fwhm)
    assert math.isnan(loaded.peaks[0].area)


def test_validate_rejects_bad_version() -> None:
    data = session_to_dict(
        Spectrum(x=[1.0, 2.0], y=[0.1, 0.2], x_unit="nm", y_unit="A")
    )
    data["format_version"] = 99
    with pytest.raises(SessionError, match="unsupported format_version"):
        validate_session_dict(data)


def test_validate_rejects_missing_spectrum() -> None:
    with pytest.raises(SessionError, match="missing spectrum"):
        validate_session_dict({"format_version": 1})


def test_validate_rejects_x_y_mismatch() -> None:
    data = {
        "format_version": 1,
        "spectrum": {
            "x": [1.0, 2.0],
            "y": [0.1],
            "x_unit": "nm",
            "y_unit": "A",
            "title": "",
            "source_path": "",
            "meta": {},
        },
    }
    with pytest.raises(SessionError, match="length mismatch"):
        session_from_dict(data)


def test_load_missing_file(tmp_path: Path) -> None:
    with pytest.raises(SessionError, match="not found"):
        load_session(tmp_path / "nope.csw.json")


def test_load_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.csw.json"
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(SessionError, match="invalid JSON"):
        load_session(path)


def test_normalize_processing_defaults() -> None:
    assert normalize_processing(None) == DEFAULT_PROCESSING
    assert normalize_processing({})["baseline_method"] == "polynomial"
    out = normalize_processing({"baseline_on": 1, "flip_y_unit": 0})
    assert out["baseline_on"] is True
    assert out["flip_y_unit"] is False


def test_build_provenance_summary() -> None:
    spec = Spectrum(
        x=[1.0, 2.0], y=[0.1, 0.2], x_unit="nm", y_unit="A", title="demo"
    )
    prov = build_provenance(
        spectrum=spec,
        source_path="/tmp/demo.csv",
        processing={"baseline_on": False},
        peak_count=3,
        package_version="0.1.0",
    )
    assert prov["source_name"] == "demo.csv"
    assert prov["baseline"] == "none"
    assert prov["peak_count"] == 3
    assert "source=demo.csv" in prov["summary"]
    assert "v=0.1.0" in prov["summary"]


def test_session_download_filename() -> None:
    assert session_download_filename(None) == "session.csw.json"
    assert session_download_filename("UV Vis!") == "UV_Vis_.csw.json"


def test_dict_round_trip_without_file() -> None:
    spec = Spectrum(
        x=np.array([1000.0, 900.0, 800.0]),
        y=np.array([0.2, 1.0, 0.3]),
        x_unit="cm-1",
        y_unit="intensity",
        title="ir_tiny",
    )
    peaks = find_peaks(spec, prominence=0.1)
    data = session_to_dict(
        spec,
        processing={"baseline_on": False, "prominence": 0.1},
        peaks=peaks,
        notes="hello",
        source_path="/somewhere/ir.csv",
    )
    again = session_from_dict(data)
    assert again.notes == "hello"
    assert again.spectrum.x_unit == "cm-1"
    np.testing.assert_allclose(again.spectrum.y, spec.y)
