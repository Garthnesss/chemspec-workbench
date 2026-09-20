"""Tests for processing pipeline ops + history round-trip + session integration."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from spectrum_core import (
    PipelineState,
    ProcessingHistory,
    ProcessingStep,
    Spectrum,
    apply_step,
    ingest_csv,
    load_session,
    make_step,
    op_baseline,
    op_despike,
    op_normalize,
    op_smooth,
    replay_history,
    save_session,
    session_from_dict,
    session_to_dict,
)
from spectrum_core.processing import (
    PIPELINE_STEPS,
    STEP_BASELINE,
    STEP_DESPIKE,
    STEP_NORMALIZE,
    STEP_SMOOTH,
)


def _synthetic_peak_spectrum(*, n: int = 201, spike: bool = False) -> Spectrum:
    x = np.linspace(400.0, 700.0, n)
    y = 0.05 + 0.8 * np.exp(-0.5 * ((x - 550.0) / 15.0) ** 2)
    y = y + 0.0005 * (x - 400.0)  # mild continuum
    if spike:
        y = y.copy()
        y[n // 2] = y[n // 2] + 5.0
    return Spectrum(x=x, y=y, x_unit="nm", y_unit="A", title="synth")


def test_pipeline_steps_catalog() -> None:
    assert STEP_BASELINE in PIPELINE_STEPS
    assert STEP_SMOOTH in PIPELINE_STEPS
    assert STEP_DESPIKE in PIPELINE_STEPS
    assert STEP_NORMALIZE in PIPELINE_STEPS


def test_op_baseline_does_not_mutate_raw(uvvis_csv: Path) -> None:
    raw = ingest_csv(
        uvvis_csv,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    y_before = raw.y.copy()
    corrected = op_baseline(raw, method="polynomial", degree=2)
    np.testing.assert_array_equal(raw.y, y_before)
    assert corrected is not raw
    assert not np.allclose(corrected.y, raw.y)
    assert corrected.meta.get("baseline_method") == "polynomial"


def test_op_smooth_savgol_reduces_noise() -> None:
    rng = np.random.default_rng(0)
    x = np.linspace(0, 10, 101)
    clean = np.sin(x)
    noisy = clean + 0.3 * rng.normal(size=clean.shape)
    spec = Spectrum(x=x, y=noisy, x_unit="nm", y_unit="intensity", title="noisy")
    y_before = spec.y.copy()
    smoothed = op_smooth(spec, window_length=11, polyorder=3)
    np.testing.assert_array_equal(spec.y, y_before)
    # Smoothed should be closer to clean than noisy
    err_noisy = float(np.mean((noisy - clean) ** 2))
    err_smooth = float(np.mean((smoothed.y - clean) ** 2))
    assert err_smooth < err_noisy
    assert smoothed.meta["smooth_method"] == "savgol"


def test_op_smooth_rejects_even_window() -> None:
    spec = _synthetic_peak_spectrum()
    with pytest.raises(ValueError, match="odd"):
        op_smooth(spec, window_length=10, polyorder=2)


def test_op_despike_removes_outlier() -> None:
    spec = _synthetic_peak_spectrum(spike=True)
    mid = len(spec) // 2
    assert spec.y[mid] > 4.0
    y_before = spec.y.copy()
    cleaned = op_despike(spec, window=5, z_thresh=4.0)
    np.testing.assert_array_equal(spec.y, y_before)
    assert cleaned.y[mid] < 2.0
    assert cleaned.meta.get("despike_replaced", 0) >= 1


def test_op_normalize_max() -> None:
    spec = _synthetic_peak_spectrum()
    y_before = spec.y.copy()
    normed = op_normalize(spec, mode="max")
    np.testing.assert_array_equal(spec.y, y_before)
    assert float(np.nanmax(np.abs(normed.y))) == pytest.approx(1.0)
    assert normed.meta["normalize_mode"] == "max"
    assert normed.meta["normalize_scale"] > 0


def test_op_normalize_area() -> None:
    spec = _synthetic_peak_spectrum()
    normed = op_normalize(spec, mode="area")
    finite = np.isfinite(normed.x) & np.isfinite(normed.y)
    area = float(np.trapezoid(np.abs(normed.y[finite]), normed.x[finite]))
    assert area == pytest.approx(1.0, rel=1e-6)
    assert normed.meta["normalize_mode"] == "area"


def test_op_normalize_unknown_mode() -> None:
    with pytest.raises(ValueError, match="unknown normalize mode"):
        op_normalize(_synthetic_peak_spectrum(), mode="l2")


def test_apply_step_appends_history_keeps_raw() -> None:
    raw = _synthetic_peak_spectrum()
    hist = ProcessingHistory()
    working, hist2 = apply_step(
        raw, hist, make_step("smooth", {"window_length": 9, "polyorder": 2})
    )
    assert len(hist) == 0  # original history unchanged
    assert len(hist2) == 1
    assert hist2.steps[0].name == "smooth"
    assert hist2.steps[0].params["window_length"] == 9
    assert hist2.steps[0].timestamp
    assert hist2.steps[0].software_note
    np.testing.assert_allclose(raw.y, _synthetic_peak_spectrum().y)
    assert not np.allclose(working.y, raw.y)


def test_apply_step_string_name() -> None:
    raw = _synthetic_peak_spectrum()
    working, hist = apply_step(raw, None, "normalize", {"mode": "max"})
    assert len(hist) == 1
    assert hist.steps[0].name == "normalize"
    assert float(np.nanmax(np.abs(working.y))) == pytest.approx(1.0)


def test_apply_step_unknown() -> None:
    with pytest.raises(ValueError, match="unknown pipeline step"):
        apply_step(_synthetic_peak_spectrum(), None, "fft")


def test_pipeline_state_raw_vs_working() -> None:
    raw = _synthetic_peak_spectrum(spike=True)
    state = PipelineState.from_raw(raw)
    np.testing.assert_allclose(state.raw.y, state.working.y)
    state2 = state.apply("despike", {"window": 5, "z_thresh": 4.0})
    assert state2.raw is state.raw or np.allclose(state2.raw.y, raw.y)
    np.testing.assert_allclose(state.raw.y, raw.y)
    assert not np.allclose(state2.working.y, raw.y)
    assert len(state2.history) == 1
    reset = state2.reset_to_raw()
    np.testing.assert_allclose(reset.working.y, raw.y)
    assert len(reset.history) == 0


def test_replay_history_matches_sequential() -> None:
    raw = _synthetic_peak_spectrum(spike=True)
    hist = ProcessingHistory()
    w, hist = apply_step(raw, hist, "despike", {"window": 5, "z_thresh": 5.0})
    w, hist = apply_step(w, hist, "smooth", {"window_length": 11, "polyorder": 3})
    w, hist = apply_step(w, hist, "normalize", {"mode": "max"})
    replayed, rebuilt = replay_history(raw, hist)
    np.testing.assert_allclose(replayed.y, w.y)
    assert len(rebuilt) == len(hist)
    assert [s.name for s in rebuilt.steps] == [s.name for s in hist.steps]


def test_history_to_from_list_round_trip() -> None:
    step = ProcessingStep(
        name="baseline",
        params={"method": "polynomial", "degree": 2},
        timestamp="2026-09-19T12:00:00Z",
        software_note="test",
    )
    hist = ProcessingHistory(steps=[step])
    data = hist.to_list()
    assert data[0]["name"] == "baseline"
    back = ProcessingHistory.from_list(data)
    assert len(back) == 1
    assert back.steps[0].params["degree"] == 2
    assert back.steps[0].timestamp == "2026-09-19T12:00:00Z"


def test_session_stores_history_round_trip(tmp_path: Path) -> None:
    raw = _synthetic_peak_spectrum()
    working, hist = apply_step(
        raw, None, "smooth", {"window_length": 9, "polyorder": 2}
    )
    working, hist = apply_step(working, hist, "normalize", {"mode": "max"})
    path = tmp_path / "pipe.csw.json"
    save_session(
        path,
        raw,
        history=hist,
        processing={"baseline_on": False},
        notes="pipeline demo",
    )
    raw_json = json.loads(path.read_text(encoding="utf-8"))
    assert "history" in raw_json
    assert len(raw_json["history"]) == 2
    assert raw_json["history"][0]["name"] == "smooth"
    assert raw_json["history"][1]["name"] == "normalize"

    loaded = load_session(path)
    assert len(loaded.history) == 2
    # Embedded spectrum is raw
    np.testing.assert_allclose(loaded.spectrum.y, raw.y)
    replayed, _ = replay_history(loaded.spectrum, loaded.history)
    np.testing.assert_allclose(replayed.y, working.y)


def test_session_missing_history_defaults_empty() -> None:
    """Backward compatible: old sessions without history still load."""
    payload = session_to_dict(
        Spectrum(x=[1.0, 2.0, 3.0], y=[0.1, 0.5, 0.2], x_unit="nm", y_unit="A")
    )
    # Simulate legacy file without history key
    payload.pop("history", None)
    data = session_from_dict(payload)
    assert len(data.history) == 0


def test_history_summary_lines() -> None:
    hist = ProcessingHistory(
        steps=[
            make_step("smooth", {"window_length": 11, "polyorder": 3}),
            make_step("normalize", {"mode": "area"}),
        ]
    )
    lines = hist.summary_lines()
    assert len(lines) == 2
    assert "smooth" in lines[0]
    assert "normalize" in lines[1]
