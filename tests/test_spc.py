"""Galactic SPC ingest — first subfile, new little-endian 0x4B."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from spectrum_core import (
    Spectrum,
    apply_step,
    ingest,
    ingest_spc,
    list_spectrum_files,
    write_spc_even_x,
)
from spectrum_core.spc import ingest_spc as ingest_spc_mod


def test_roundtrip_even_x_absorbance(tmp_path: Path) -> None:
    x = np.linspace(400.0, 700.0, 61)
    y = np.exp(-0.5 * ((x - 550.0) / 20.0) ** 2)
    path = tmp_path / "dye.spc"
    write_spc_even_x(path, x, y, x_type=3, y_type=2)
    spec = ingest(path)
    assert spec.x_unit == "nm"
    assert spec.y_unit == "A"
    np.testing.assert_allclose(spec.x, x, rtol=1e-5)
    np.testing.assert_allclose(spec.y, y, rtol=1e-5, atol=1e-6)
    assert spec.meta["source_format"] == "spc"


def test_wavenumber_x_type(tmp_path: Path) -> None:
    x = np.linspace(4000.0, 400.0, 50)
    y = np.linspace(0.1, 0.2, 50)
    path = tmp_path / "ir.spc"
    write_spc_even_x(path, x, y, x_type=1, y_type=2)
    spec = ingest_spc(path)
    assert spec.x_unit == "cm-1"


def test_rejects_short_file(tmp_path: Path) -> None:
    p = tmp_path / "bad.spc"
    p.write_bytes(b"SPC")
    with pytest.raises(ValueError, match="too short"):
        ingest_spc_mod(p)


def test_pipeline_derivative_step() -> None:
    x = np.linspace(0, 10, 51)
    spec = Spectrum(x=x, y=np.sin(x), x_unit="nm", y_unit="intensity")
    out, hist = apply_step(
        spec, None, "derivative", {"order": 1, "window_length": 7, "polyorder": 3}
    )
    assert hist.steps[-1].name == "derivative"
    assert out.meta["derivative_order"] == 1


def test_folder_lists_spc(tmp_path: Path) -> None:
    x = np.linspace(0, 1, 10)
    write_spc_even_x(tmp_path / "a.spc", x, x)
    names = {p.name for p in list_spectrum_files(tmp_path)}
    assert "a.spc" in names


def test_ui_accepts_spc_and_has_derivative_button() -> None:
    text = Path(__file__).resolve().parents[1].joinpath("chemspec", "ui_app.py").read_text(
        encoding="utf-8"
    )
    assert ".spc" in text
    assert "on_apply_derivative_step" in text
    assert "Apply derivative" in text
