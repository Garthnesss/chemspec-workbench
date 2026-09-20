"""CSV/JCAMP ingest hardening: ugly real-world edge cases."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from spectrum_core import (
    ensure_ascending_x,
    ingest,
    ingest_csv,
    ingest_jcamp,
    x_direction,
    y_unit_from_header,
)

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / "fixtures" / "ingest_edge"


@pytest.fixture
def edge_dir() -> Path:
    assert EDGE.is_dir()
    return EDGE


def test_descending_x_preserved_and_sortable(edge_dir: Path) -> None:
    path = edge_dir / "descending_x_ir.csv"
    spec = ingest_csv(
        path,
        x_col="wavenumber_cm-1",
        y_col="intensity",
        x_unit="cm-1",
        y_unit="intensity",
    )
    assert x_direction(spec.x) == "descending"
    assert spec.meta.get("x_direction") == "descending"
    assert spec.x[0] > spec.x[-1]
    sorted_spec = ensure_ascending_x(spec)
    assert x_direction(sorted_spec.x) == "ascending"
    assert sorted_spec.meta.get("x_sorted") is True
    assert sorted_spec.meta.get("x_direction_original") == "descending"
    assert sorted_spec.x[0] < sorted_spec.x[-1]
    # y follows x reorder
    assert sorted_spec.y[0] == pytest.approx(spec.y[-1])


def test_duplicate_x_retained(edge_dir: Path) -> None:
    spec = ingest_csv(
        edge_dir / "duplicate_x.csv",
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    assert len(spec) == 5
    assert np.sum(spec.x == 210.0) == 2


def test_uneven_spacing_retained(edge_dir: Path) -> None:
    spec = ingest_csv(
        edge_dir / "uneven_spacing.csv",
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    dx = np.diff(spec.x)
    assert len(np.unique(np.round(dx, 6))) > 1  # not uniform
    assert len(spec) == 6


def test_nan_inf_y_skipped_by_default(edge_dir: Path) -> None:
    spec = ingest_csv(
        edge_dir / "nan_inf_y.csv",
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    # File has 7 data rows; nan/inf/-inf → 3 skipped → 4 kept
    assert len(spec) == 4
    assert spec.meta.get("ingest_skipped_nonfinite") == 3
    assert np.all(np.isfinite(spec.y))
    assert list(spec.x) == pytest.approx([200.0, 220.0, 240.0, 260.0])


def test_nan_inf_y_kept_when_policy_off(edge_dir: Path) -> None:
    spec = ingest_csv(
        edge_dir / "nan_inf_y.csv",
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
        skip_nonfinite=False,
    )
    assert len(spec) == 7
    assert not np.all(np.isfinite(spec.y))
    assert np.isnan(spec.y[1])
    assert np.isinf(spec.y[3])


def test_semicolon_delimiter(edge_dir: Path) -> None:
    spec = ingest_csv(
        edge_dir / "semicolon_delim.csv",
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    assert len(spec) == 4
    assert spec.meta.get("delimiter") == ";"
    assert spec.x.min() == pytest.approx(200.0)


def test_tab_delimiter(edge_dir: Path) -> None:
    spec = ingest_csv(
        edge_dir / "tab_delim.tsv",
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    assert len(spec) == 4
    assert spec.meta.get("delimiter") == "\t"


def test_quoted_csv_fields(edge_dir: Path) -> None:
    spec = ingest_csv(
        edge_dir / "quoted_fields.csv",
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    assert len(spec) == 3
    assert spec.y.max() == pytest.approx(0.55)


def test_missing_values_and_extra_columns(edge_dir: Path) -> None:
    spec = ingest_csv(
        edge_dir / "missing_extra_cols.csv",
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    # rows: ok, missing y, ok, missing x, ok, ok (short row still has x/y)
    assert len(spec) == 4
    assert spec.meta.get("ingest_skipped_missing") >= 2
    assert 210.0 not in set(spec.x.tolist())


def test_percent_t_and_absorbance_headers(edge_dir: Path) -> None:
    assert y_unit_from_header("%T") == "percent_T"
    assert y_unit_from_header("Absorbance") == "A"
    assert y_unit_from_header("intensity") is None

    pct = ingest_csv(
        edge_dir / "percent_t_header.csv",
        x_col="wavenumber_cm-1",
        y_col="%T",
        x_unit="cm-1",
        y_unit=y_unit_from_header("%T") or "percent_T",
    )
    assert pct.y_unit == "percent_T"
    assert pct.y.min() == pytest.approx(40.0)

    abs_spec = ingest_csv(
        edge_dir / "absorbance_header.csv",
        x_col="wavelength_nm",
        y_col="Absorbance",
        x_unit="nm",
        y_unit=y_unit_from_header("Absorbance") or "A",
    )
    assert abs_spec.y_unit == "A"
    assert abs_spec.y.max() == pytest.approx(0.80)


def test_empty_csv_clear_error(edge_dir: Path) -> None:
    with pytest.raises(ValueError, match="empty"):
        ingest_csv(edge_dir / "empty.csv")


def test_bad_jcamp_clear_error(edge_dir: Path) -> None:
    with pytest.raises(ValueError, match="JCAMP-DX"):
        ingest_jcamp(edge_dir / "bad_minimal.jdx")


def test_ensure_ascending_noop_on_ascending() -> None:
    from spectrum_core import Spectrum

    spec = Spectrum(x=[1.0, 2.0, 3.0], y=[0.1, 0.2, 0.3])
    out = ensure_ascending_x(spec)
    assert out.meta.get("x_sorted") is not True
    assert list(out.x) == [1.0, 2.0, 3.0]


def test_ingest_dispatch_edge_csv(edge_dir: Path) -> None:
    spec = ingest(
        edge_dir / "semicolon_delim.csv",
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    assert len(spec) == 4


def test_public_pnnl_still_loads() -> None:
    """Regression: public PNNL fixtures remain ingestible (often descending x)."""
    public = ROOT / "fixtures" / "public" / "ethanol_ir_pnnl.jdx"
    spec = ingest_jcamp(public)
    assert len(spec) > 100
    assert spec.x_unit == "cm-1"
    # PNNL IR is typically high→low wavenumber; either way, helper works.
    sorted_spec = ensure_ascending_x(spec)
    assert x_direction(sorted_spec.x) == "ascending"
    assert len(sorted_spec) == len(spec)
