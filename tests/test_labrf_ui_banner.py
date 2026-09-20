"""LabRF NiceGUI disclaimer must not use removed ``ui.banner`` (NiceGUI 3.x)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_UI_APP = Path(__file__).resolve().parents[1] / "labrf" / "ui_app.py"


def test_labrf_ui_source_has_no_ui_banner() -> None:
    """Static guard: ``ui.banner`` crashes on NiceGUI 3.17+ (attr missing)."""
    src = _UI_APP.read_text(encoding="utf-8")
    assert "ui.banner" not in src
    assert "ui.card" in src
    assert "_BANNER_TEXT" in src

    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "banner":
            pytest.fail(
                f"labrf/ui_app.py references '.banner' at line {node.lineno}; "
                "use dismissible ui.card for NiceGUI 3.x compatibility"
            )


def test_labrf_build_ui_disclaimer_card_smoke() -> None:
    """Import/build LabRF UI without starting a server; must not AttributeError."""
    pytest.importorskip("nicegui")
    from nicegui import ui

    assert hasattr(ui, "card"), "NiceGUI ui.card required for LabRF disclaimer"
    # NiceGUI 3.17.x has no ui.banner — that was the crash. Prefer card either way.
    assert not hasattr(ui, "banner"), (
        "unexpected ui.banner on this NiceGUI; LabRF still must use ui.card"
    )

    from labrf.ui_app import _BANNER_TEXT, build_ui

    assert "receive-only" in _BANNER_TEXT.lower()
    assert "educational" in _BANNER_TEXT.lower()
    build_ui()  # constructs dismissible amber card; no ui.run
