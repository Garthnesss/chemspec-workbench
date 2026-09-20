"""Smoke test for examples/ethanol_ir_walkthrough.py (cheap; no nbconvert)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "examples" / "ethanol_ir_walkthrough.py"
FIXTURE = ROOT / "fixtures" / "public" / "ethanol_ir_pnnl.jdx"


@pytest.fixture(scope="module")
def walkthrough_mod():
    if not SCRIPT.is_file():
        pytest.skip(f"missing {SCRIPT}")
    spec = importlib.util.spec_from_file_location("ethanol_ir_walkthrough", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # Ensure repo root import path for spectrum_core when run oddly
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec.loader.exec_module(mod)
    return mod


def test_walkthrough_script_exists() -> None:
    assert SCRIPT.is_file()
    assert FIXTURE.is_file()
    nb = ROOT / "examples" / "ethanol_ir_walkthrough.ipynb"
    assert nb.is_file()


def test_walkthrough_run_finds_peaks(walkthrough_mod, tmp_path: Path) -> None:
    result = walkthrough_mod.run(
        repo_root=ROOT,
        save_dir=tmp_path,
        prominence=0.01,
        show_plot=False,
    )
    assert result["n_points"] > 100
    assert result["x_unit"] == "cm-1"
    assert result["n_peaks"] >= 1
    assert result["history_steps"] == ["baseline", "smooth"]
    assert Path(result["peaks_csv"]).is_file()
    assert Path(result["session"]).is_file()
    assert Path(result["figure"]).is_file()
    # Sanity: CSV header includes FWHM/area columns
    header = Path(result["peaks_csv"]).read_text(encoding="utf-8").splitlines()[0]
    assert "fwhm" in header and "area" in header
