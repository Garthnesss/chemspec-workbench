"""ChemSpec / spectrum_core PNG export (honesty footer; no compound ID)."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from spectrum_core import (
    DEFAULT_HONESTY_NOTE,
    export_spectrum_png,
    export_waterfall_png,
    find_peaks,
    ingest,
    ingest_csv,
)
from spectrum_core.export_png import _is_log_epsilon_meta, _y_label


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "fixtures" / "public"


def test_default_honesty_note_disclaims_compound_id():
    assert "compound-ID" in DEFAULT_HONESTY_NOTE or "compound ID" in DEFAULT_HONESTY_NOTE.lower()
    assert "ChemSpec" in DEFAULT_HONESTY_NOTE


def test_export_spectrum_png_writes_file(tmp_path: Path, uvvis_csv: Path):
    spec = ingest_csv(
        uvvis_csv,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    peaks = find_peaks(spec, prominence=0.15)
    out = tmp_path / "uvvis.png"
    path = export_spectrum_png(spec, out, peaks=peaks)
    assert path == out
    assert out.is_file()
    assert out.stat().st_size > 500
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_export_spectrum_png_bytesio_and_ir_reverse(tmp_path: Path, ir_csv: Path):
    spec = ingest_csv(
        ir_csv,
        x_col="wavenumber_cm-1",
        y_col="intensity",
        x_unit="cm-1",
        y_unit="intensity",
    )
    buf = io.BytesIO()
    result = export_spectrum_png(spec, buf, title="IR synthetic demo")
    assert result is None
    data = buf.getvalue()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 500


def test_export_spectrum_png_log_eps_caption():
    path = PUBLIC / "benzene_uvvis_nist.jdx"
    if not path.is_file():
        pytest.skip("missing public benzene UV-Vis fixture")
    spec = ingest(path)
    assert _is_log_epsilon_meta(spec.meta)
    assert "log" in _y_label(spec.y_unit, spec.meta).lower()
    assert "not absorbance" in _y_label(spec.y_unit, spec.meta).lower()
    buf = io.BytesIO()
    export_spectrum_png(spec, buf, honesty_note=DEFAULT_HONESTY_NOTE)
    assert buf.getvalue()[:8] == b"\x89PNG\r\n\x1a\n"


def test_export_waterfall_png(tmp_path: Path, uvvis_csv: Path):
    a = ingest_csv(
        uvvis_csv,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
        title="trace_a",
    )
    b = a.with_y(a.y * 0.9, title="trace_b")
    out = tmp_path / "waterfall.png"
    path = export_waterfall_png([a, b], out)
    assert path == out
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_export_waterfall_png_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        export_waterfall_png([], io.BytesIO())


def test_package_exports():
    import spectrum_core

    assert hasattr(spectrum_core, "export_spectrum_png")
    assert hasattr(spectrum_core, "export_waterfall_png")
    assert hasattr(spectrum_core, "DEFAULT_HONESTY_NOTE")


def test_png_export_filename():
    from chemspec.ui_helpers import png_export_filename

    assert png_export_filename(None) == "chemspec_spectrum.png"
    assert png_export_filename("Benzene UV-Vis") == "Benzene_UV-Vis_spectrum.png"
