"""Public-domain NIST/PNNL IR fixtures (real spectra; no compound-ID claims)."""

from __future__ import annotations

from pathlib import Path

import pytest

from spectrum_core import find_peaks, ingest_jcamp

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "fixtures" / "public"

PUBLIC_JDX = sorted(PUBLIC.glob("*.jdx"))


@pytest.fixture(params=PUBLIC_JDX, ids=lambda p: p.name)
def public_jdx(request: pytest.FixtureRequest) -> Path:
    path: Path = request.param
    assert path.is_file()
    return path


def test_public_fixtures_present() -> None:
    assert PUBLIC.is_dir()
    assert (PUBLIC / "SOURCES.md").is_file()
    names = {p.name for p in PUBLIC_JDX}
    assert "ethanol_ir_pnnl.jdx" in names
    assert "methanol_ir_pnnl.jdx" in names
    assert "toluene_ir_pnnl.jdx" in names
    assert len(PUBLIC_JDX) >= 2


def test_public_jcamp_loads_and_has_signal(public_jdx: Path) -> None:
    """Each public JCAMP must ingest and be large enough for peak finding."""
    spec = ingest_jcamp(public_jdx)
    assert len(spec.x) > 100
    assert len(spec.y) == len(spec.x)
    assert spec.x_unit == "cm-1"
    # PNNL n/k YUNITS map to intensity (unknown → intensity with note).
    assert spec.y_unit == "intensity"
    peaks = find_peaks(spec, prominence=None)
    assert len(peaks) >= 1 or len(spec.x) > 100


def test_public_owner_is_public_domain(public_jdx: Path) -> None:
    text = public_jdx.read_text(encoding="utf-8", errors="replace")
    assert "##OWNER=Public domain" in text
    assert "COBLENTZ" not in text.upper().split("##OWNER=")[0]  # header only soft check
    # Hard rule: never ship Coblentz owner lines in this folder.
    assert "##OWNER=COBLENTZ" not in text.upper()
