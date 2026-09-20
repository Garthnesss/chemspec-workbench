"""Regression: loading a new fixture must not keep the prior working spectrum."""

from __future__ import annotations

from chemspec.ui_app import (
    WorkbenchState,
    _build_figure,
    _load_fixture,
    _reset_pipeline,
    _working_spectrum,
)
from spectrum_core.processing import ProcessingHistory, apply_step


def test_ethanol_then_benzene_clears_stale_working() -> None:
    state = WorkbenchState()
    _load_fixture(state, "public_ethanol_ir")
    assert state.primary is not None
    assert state.primary.x_unit == "cm-1"

    _reset_pipeline(state)
    assert state.working is not None
    state.working, state.history = apply_step(
        state.working, state.history, "smooth", {"window": 11, "polyorder": 3}
    )
    assert len(state.history) >= 1
    stale_n = len(state.working)

    _load_fixture(state, "public_benzene_uvvis")
    assert state.error == ""
    assert state.primary is not None
    assert state.primary.x_unit == "nm"
    assert len(state.history) == 0
    assert state.working is not None
    assert len(state.working) == len(state.primary)
    assert len(state.working) != stale_n

    work = _working_spectrum(state, state.primary)
    assert work is not None
    assert work.x_unit == "nm"
    fig = _build_figure(state)
    assert abs(float(fig.data[0].x[0]) - float(state.primary.x[0])) < 1e-6


def test_working_spectrum_guard_repairs_stale_buffer() -> None:
    state = WorkbenchState()
    _load_fixture(state, "public_ethanol_ir")
    _reset_pipeline(state)
    stale = state.working
    assert stale is not None

    _load_fixture(state, "public_benzene_uvvis")
    # Poison working after load to exercise the defensive guard.
    state.working = stale
    state.history = ProcessingHistory()

    work = _working_spectrum(state, state.primary)
    assert work is not None
    assert work.x_unit == "nm"
    assert len(work) == len(state.primary)
