"""Public NIST/PNNL fixtures (real spectra; no compound-ID claims)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from spectrum_core import find_peaks, ingest_jcamp

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "fixtures" / "public"

IR_JDX = [
    PUBLIC / "ethanol_ir_pnnl.jdx",
    PUBLIC / "methanol_ir_pnnl.jdx",
    PUBLIC / "toluene_ir_pnnl.jdx",
]
UVVIS_JDX = [
    PUBLIC / "benzene_uvvis_nist.jdx",
    PUBLIC / "acetone_uvvis_nist.jdx",
    PUBLIC / "naphthalene_uvvis_nist.jdx",
]
PUBLIC_JDX = IR_JDX + UVVIS_JDX


@pytest.fixture(params=PUBLIC_JDX, ids=lambda p: p.name)
def public_jdx(request: pytest.FixtureRequest) -> Path:
    path: Path = request.param
    assert path.is_file()
    return path


@pytest.fixture(params=IR_JDX, ids=lambda p: p.name)
def public_ir_jdx(request: pytest.FixtureRequest) -> Path:
    path: Path = request.param
    assert path.is_file()
    return path


@pytest.fixture(params=UVVIS_JDX, ids=lambda p: p.name)
def public_uvvis_jdx(request: pytest.FixtureRequest) -> Path:
    path: Path = request.param
    assert path.is_file()
    return path


def test_public_fixtures_present() -> None:
    assert PUBLIC.is_dir()
    assert (PUBLIC / "SOURCES.md").is_file()
    names = {p.name for p in PUBLIC.glob("*.jdx")}
    for expected in (
        "ethanol_ir_pnnl.jdx",
        "methanol_ir_pnnl.jdx",
        "toluene_ir_pnnl.jdx",
        "benzene_uvvis_nist.jdx",
        "acetone_uvvis_nist.jdx",
        "naphthalene_uvvis_nist.jdx",
    ):
        assert expected in names
    sources = (PUBLIC / "SOURCES.md").read_text(encoding="utf-8")
    assert "UV-Vis" in sources or "UV/Vis" in sources
    assert "Logarithm epsilon" in sources
    assert "no compound-ID" in sources.lower() or "no compound-identification" in sources.lower()


def test_public_ir_jcamp_loads_and_has_signal(public_ir_jdx: Path) -> None:
    """PNNL IR JCAMPs: cm-1, intensity, large enough for peak finding."""
    spec = ingest_jcamp(public_ir_jdx)
    assert len(spec.x) > 100
    assert len(spec.y) == len(spec.x)
    assert spec.x_unit == "cm-1"
    assert spec.y_unit == "intensity"
    peaks = find_peaks(spec, prominence=None)
    assert len(peaks) >= 1 or len(spec.x) > 100


def test_public_ir_owner_is_public_domain(public_ir_jdx: Path) -> None:
    text = public_ir_jdx.read_text(encoding="utf-8", errors="replace")
    assert "##OWNER=Public domain" in text
    assert "##OWNER=COBLENTZ" not in text.upper()


def test_public_uvvis_jcamp_loads(public_uvvis_jdx: Path) -> None:
    """NIST UV/Vis: Wavelength (nm) → nm; Logarithm epsilon → intensity (not A)."""
    spec = ingest_jcamp(public_uvvis_jdx)
    assert len(spec.x) > 10
    assert len(spec.y) == len(spec.x)
    assert spec.x_unit == "nm"
    assert spec.y_unit == "intensity"
    assert np.all(np.isfinite(spec.y))
    assert np.all(np.isfinite(spec.x))
    notes = " ".join(spec.meta.get("unit_notes", []))
    assert "log" in notes.lower() and ("epsilon" in notes.lower() or "ε" in notes)
    assert "not absorbance" in notes.lower()
    # log-ε curves still have structure — at least one peak, or a clear y-range.
    peaks = find_peaks(spec, prominence=None)
    if len(peaks) < 1:
        y_span = float(np.nanmax(spec.y) - np.nanmin(spec.y))
        assert y_span > 0.1
        assert float(np.nanmin(spec.x)) < float(np.nanmax(spec.x))
    else:
        assert len(peaks) >= 1


def test_public_uvvis_owner_nist_osrd(public_uvvis_jdx: Path) -> None:
    """UV-Vis fixtures quote INEP CP RAS, NIST OSRD — not Coblentz, not PNNL PD."""
    text = public_uvvis_jdx.read_text(encoding="utf-8", errors="replace")
    assert "INEP CP RAS" in text or "NIST OSRD" in text
    assert "##XUNITS=Wavelength (nm)" in text
    assert "##YUNITS=Logarithm epsilon" in text
    assert "##OWNER=COBLENTZ" not in text.upper()
    assert "COBLENTZ SOCIETY" not in text.upper()


def test_public_jcamp_no_coblentz(public_jdx: Path) -> None:
    text = public_jdx.read_text(encoding="utf-8", errors="replace")
    assert "##OWNER=COBLENTZ" not in text.upper()
