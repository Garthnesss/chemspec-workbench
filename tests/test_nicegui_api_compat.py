"""Guard ChemSpec / LabRF / TeachSpec NiceGUI UIs against missing ``ui.*`` attrs (API drift)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_UI_MODULES = (
    _ROOT / "labrf" / "ui_app.py",
    _ROOT / "chemspec" / "ui_app.py",
    _ROOT / "teachspec" / "ui_app.py",
)


def _ui_attrs_used(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    attrs: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "ui"
        ):
            attrs.add(node.attr)
    return attrs


@pytest.mark.parametrize("ui_path", _UI_MODULES, ids=lambda p: p.parent.name)
def test_ui_module_attrs_exist_on_nicegui(ui_path: Path) -> None:
    """Every ``ui.foo`` reference in our UI modules must exist on installed NiceGUI."""
    pytest.importorskip("nicegui")
    from nicegui import ui

    used = _ui_attrs_used(ui_path)
    assert used, f"expected ui.* usage in {ui_path}"
    missing = sorted(a for a in used if not hasattr(ui, a))
    assert not missing, (
        f"{ui_path.relative_to(_ROOT)} references missing NiceGUI attrs: {missing}. "
        "Pin/adapt for the installed NiceGUI major (see LabRF ui.banner → ui.card)."
    )


def test_labrf_and_chemspec_avoid_removed_banner() -> None:
    """``ui.banner`` is absent on NiceGUI 3.17+; TeachSpec/LabRF/ChemSpec must not call it."""
    for path in _UI_MODULES:
        src = path.read_text(encoding="utf-8")
        assert "ui.banner" not in src, path
