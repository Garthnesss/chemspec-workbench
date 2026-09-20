"""NiceGUI peak table rows include Peak contract fields."""

from __future__ import annotations

from chemspec.ui_app import WorkbenchState, _peak_rows
from spectrum_core.peaks import Peak


def test_peak_rows_include_baseline_ref() -> None:
    state = WorkbenchState()
    state.peaks = [
        Peak(
            index=3,
            x=1050.0,
            y=1.2,
            prominence=0.8,
            fwhm=12.0,
            area=5.0,
            half_max_level=0.8,
            left_boundary_x=1040.0,
            right_boundary_x=1060.0,
            baseline_reference_note="prominence-relative half-max (not absolute zero)",
        )
    ]
    rows = _peak_rows(state)
    assert len(rows) == 1
    assert rows[0]["width_def"]
    assert "prominence-relative" in rows[0]["baseline_ref"]
