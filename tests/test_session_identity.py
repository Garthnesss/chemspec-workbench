"""Session raw_data_hash / analysis_fingerprint stability + v1 migration."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from spectrum_core import (
    SESSION_FORMAT_VERSION,
    Peak,
    Spectrum,
    compute_analysis_fingerprint,
    compute_raw_data_hash,
    load_session,
    migrate_session_dict,
    save_session,
    session_from_dict,
    session_to_dict,
)
from spectrum_core.processing import ProcessingHistory, ProcessingStep
from spectrum_core.session import (
    SESSION_FORMAT_VERSION_MIN,
    compute_source_path_hash,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "sessions"


def _tiny_spec() -> Spectrum:
    return Spectrum(
        x=np.array([1.0, 2.0, 3.0]),
        y=np.array([0.1, 0.8, 0.2]),
        x_unit="nm",
        y_unit="A",
        title="tiny",
    )


def test_raw_data_hash_stable_across_calls() -> None:
    spec = _tiny_spec()
    a = compute_raw_data_hash(spec)
    b = compute_raw_data_hash(spec.copy())
    assert a == b
    assert len(a) == 64
    # Different y → different hash
    other = Spectrum(x=spec.x.copy(), y=spec.y + 0.01, x_unit="nm", y_unit="A")
    assert compute_raw_data_hash(other) != a


def test_raw_data_hash_nan_encoding_stable() -> None:
    spec = Spectrum(
        x=np.array([1.0, 2.0, 3.0]),
        y=np.array([0.1, np.nan, 0.2]),
        x_unit="nm",
        y_unit="intensity",
    )
    assert compute_raw_data_hash(spec) == compute_raw_data_hash(spec.copy())


def test_analysis_fingerprint_ignores_history_timestamps() -> None:
    spec = _tiny_spec()
    rdh = compute_raw_data_hash(spec)
    hist_a = ProcessingHistory(
        steps=[
            ProcessingStep(
                name="smooth",
                params={"window_length": 5, "polyorder": 2},
                timestamp="2020-01-01T00:00:00Z",
            )
        ]
    )
    hist_b = ProcessingHistory(
        steps=[
            ProcessingStep(
                name="smooth",
                params={"window_length": 5, "polyorder": 2},
                timestamp="2099-12-31T23:59:59Z",
            )
        ]
    )
    fp_a = compute_analysis_fingerprint(
        raw_data_hash=rdh,
        x_unit=spec.x_unit,
        y_unit=spec.y_unit,
        processing={"baseline_on": False},
        history=hist_a,
        peaks=[],
    )
    fp_b = compute_analysis_fingerprint(
        raw_data_hash=rdh,
        x_unit=spec.x_unit,
        y_unit=spec.y_unit,
        processing={"baseline_on": False},
        history=hist_b,
        peaks=[],
    )
    assert fp_a == fp_b

    # Changing params must change fingerprint
    hist_c = ProcessingHistory(
        steps=[
            ProcessingStep(
                name="smooth",
                params={"window_length": 7, "polyorder": 2},
                timestamp="2020-01-01T00:00:00Z",
            )
        ]
    )
    fp_c = compute_analysis_fingerprint(
        raw_data_hash=rdh,
        x_unit=spec.x_unit,
        y_unit=spec.y_unit,
        processing={"baseline_on": False},
        history=hist_c,
        peaks=[],
    )
    assert fp_c != fp_a


def test_session_to_dict_embeds_identity_fields() -> None:
    spec = _tiny_spec()
    peaks = [Peak(index=1, x=2.0, y=0.8, prominence=0.5, fwhm=1.0, area=0.4)]
    payload = session_to_dict(
        spec,
        peaks=peaks,
        source_path="/tmp/demo.csv",
        notes="hello",
    )
    assert payload["format_version"] == SESSION_FORMAT_VERSION
    assert payload["raw_data_hash"] == compute_raw_data_hash(spec)
    assert payload["source_path_hash"] == compute_source_path_hash("/tmp/demo.csv")
    assert len(payload["analysis_fingerprint"]) == 64
    # Notes are not part of computational identity — changing notes keeps same fp
    # when rebuilt with same hash inputs:
    fp = compute_analysis_fingerprint(
        raw_data_hash=payload["raw_data_hash"],
        x_unit=spec.x_unit,
        y_unit=spec.y_unit,
        processing=payload["processing"],
        history=payload["history"],
        peaks=peaks,
        source_path_hash=payload["source_path_hash"],
    )
    assert payload["analysis_fingerprint"] == fp


def test_session_round_trip_preserves_hashes(tmp_path: Path) -> None:
    spec = _tiny_spec()
    path = tmp_path / "id.csw.json"
    save_session(path, spec, source_path="/data/a.csv", notes="n1")
    loaded = load_session(path)
    assert loaded.format_version == SESSION_FORMAT_VERSION
    assert loaded.raw_data_hash == compute_raw_data_hash(spec)
    assert loaded.source_path_hash == compute_source_path_hash("/data/a.csv")
    assert loaded.analysis_fingerprint
    # Re-save with different notes → same computational hashes
    path2 = tmp_path / "id2.csw.json"
    save_session(path2, spec, source_path="/data/a.csv", notes="n2 DIFFERENT")
    loaded2 = load_session(path2)
    assert loaded2.raw_data_hash == loaded.raw_data_hash
    assert loaded2.analysis_fingerprint == loaded.analysis_fingerprint


def test_migrate_v1_fixture_adds_hashes() -> None:
    raw = json.loads((FIXTURES / "session_v1.json").read_text(encoding="utf-8"))
    assert raw["format_version"] == 1
    assert "raw_data_hash" not in raw
    migrated = migrate_session_dict(raw)
    assert migrated["format_version"] == SESSION_FORMAT_VERSION
    assert len(migrated["raw_data_hash"]) == 64
    assert len(migrated["analysis_fingerprint"]) == 64
    assert migrated["source_path_hash"] == compute_source_path_hash(
        raw["spectrum"]["source_path"]
    )
    # History timestamps retained
    assert migrated["history"][0]["timestamp"] == "2026-01-01T00:00:00Z"


def test_load_v1_fixture_migrates() -> None:
    loaded = load_session(FIXTURES / "session_v1.json")
    assert loaded.format_version == SESSION_FORMAT_VERSION
    assert loaded.raw_data_hash
    assert loaded.analysis_fingerprint
    assert loaded.spectrum.title == "session_v1 fixture"
    assert len(loaded.history) == 1


def test_load_v2_fixture() -> None:
    loaded = load_session(FIXTURES / "session_v2.json")
    assert loaded.format_version == SESSION_FORMAT_VERSION
    assert loaded.raw_data_hash == compute_raw_data_hash(loaded.spectrum)
    # Fingerprint in file should match recomputation
    again = compute_analysis_fingerprint(
        raw_data_hash=loaded.raw_data_hash,
        x_unit=loaded.spectrum.x_unit,
        y_unit=loaded.spectrum.y_unit,
        processing=loaded.processing,
        history=loaded.history,
        peaks=loaded.peaks,
        source_path_hash=loaded.source_path_hash,
    )
    assert loaded.analysis_fingerprint == again


def test_migrate_idempotent_on_current() -> None:
    spec = _tiny_spec()
    payload = session_to_dict(spec)
    again = migrate_session_dict(payload)
    assert again["raw_data_hash"] == payload["raw_data_hash"]
    assert again["analysis_fingerprint"] == payload["analysis_fingerprint"]


def test_format_version_min_documented() -> None:
    assert SESSION_FORMAT_VERSION_MIN == 1
    assert SESSION_FORMAT_VERSION >= 2
