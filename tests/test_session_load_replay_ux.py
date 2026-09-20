"""Session load auto-replays pipeline history (NiceGUI workbench UX)."""

from __future__ import annotations

from pathlib import Path

from chemspec.ui_app import WorkbenchState, _load_session_path

_SESSIONS = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "sessions"


def test_load_session_auto_replays_history_and_status() -> None:
    state = WorkbenchState()
    path = _SESSIONS / "session_v2.json"
    _load_session_path(state, path)
    assert state.error == ""
    assert state.primary is not None
    assert len(state.history) >= 1
    assert state.working is not None
    # Live baseline toggle cleared so history owns processing
    assert state.baseline_on is False
    assert "replayed" in state.status.lower()
    assert "raw" in state.status.lower()
    assert str(len(state.history)) in state.status or "step" in state.status.lower()


def test_load_session_without_history_notes_raw_copy(tmp_path: Path) -> None:
    """Empty history → working is raw copy; status says so."""
    import json

    src = json.loads((_SESSIONS / "session_v2.json").read_text())
    src["history"] = []
    # fingerprints optional for UI load path
    out = tmp_path / "empty_hist.csw.json"
    out.write_text(json.dumps(src))
    state = WorkbenchState()
    _load_session_path(state, out)
    assert state.error == ""
    assert len(state.history) == 0
    assert "no pipeline history" in state.status.lower()
