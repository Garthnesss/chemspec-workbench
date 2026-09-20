"""Smoke test for examples/fidnmr_walkthrough.py (cheap; no nbconvert)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "examples" / "fidnmr_walkthrough.py"


@pytest.fixture(scope="module")
def walkthrough_mod():
    if not SCRIPT.is_file():
        pytest.skip(f"missing {SCRIPT}")
    spec = importlib.util.spec_from_file_location("fidnmr_walkthrough", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec.loader.exec_module(mod)
    return mod


def test_walkthrough_script_exists() -> None:
    assert SCRIPT.is_file()
    # Thin Phase-0 twin: .py + pytest only (notebook deferred)


def test_walkthrough_run_finds_peaks(walkthrough_mod, tmp_path: Path) -> None:
    result = walkthrough_mod.run(
        repo_root=ROOT,
        save_dir=tmp_path,
        npts=2048,
        lb_hz=1.0,
        phc0_deg=0.0,
        show_plot=False,
    )
    assert result["synthetic"] is True
    assert result["x_unit"] == "ppm"
    assert result["n_points"] == 2048
    assert result["n_peaks"] >= 2
    # Teaching mock should recover lines near the expected ppm set
    found = [p.x for p in result["peaks"]]
    for expected in result["expected_peaks_ppm"]:
        assert any(abs(f - expected) < 0.2 for f in found), (
            f"missing peak near {expected} ppm; found={found}"
        )
    assert Path(result["peaks_csv"]).is_file()
    assert Path(result["figure"]).is_file()
    header = Path(result["peaks_csv"]).read_text(encoding="utf-8").splitlines()[0]
    assert "fwhm" in header and "area" in header
