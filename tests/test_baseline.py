"""Baseline reduces continuum without deleting peaks entirely."""

import sys

import numpy as np
import pytest

from spectrum_core import (
    METHOD_ASLS,
    METHOD_MPLS,
    METHOD_POLYNOMIAL,
    available_baseline_methods,
    baseline_correct,
    baseline_polynomial,
    find_peaks,
    has_pybaselines,
    ingest_csv,
)


def test_baseline_reduces_continuum_keeps_peaks(uvvis_csv):
    spec = ingest_csv(
        uvvis_csv,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    # Emphasize continuum: ends are relatively flat vs peaks
    ends = np.concatenate([spec.y[:30], spec.y[-30:]])
    continuum_before = float(np.mean(ends))

    corrected = baseline_polynomial(spec, degree=2)
    ends_after = np.concatenate([corrected.y[:30], corrected.y[-30:]])
    continuum_after = float(np.abs(np.mean(ends_after)))

    assert continuum_after < continuum_before or continuum_after < 0.08, (
        f"continuum not reduced: before={continuum_before}, after={continuum_after}"
    )

    peaks = find_peaks(corrected, prominence=0.15)
    xs = [p.x for p in peaks]
    assert any(abs(x - 280) <= 10 for x in xs), f"lost ~280 peak: {xs}"
    assert any(abs(x - 350) <= 12 for x in xs), f"lost ~350 peak: {xs}"

    # Peak heights should remain substantial (not wiped)
    for target in (280, 350):
        near = [p for p in peaks if abs(p.x - target) <= 12]
        assert near, f"no peak near {target}"
        assert near[0].y > 0.2, f"peak near {target} too small: {near[0].y}"


def test_baseline_correct_polynomial_default(uvvis_csv):
    spec = ingest_csv(
        uvvis_csv,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    via_api = baseline_correct(spec, method=METHOD_POLYNOMIAL, degree=2)
    via_poly = baseline_polynomial(spec, degree=2)
    np.testing.assert_allclose(via_api.y, via_poly.y)
    assert via_api.meta["baseline_method"] == METHOD_POLYNOMIAL
    assert METHOD_POLYNOMIAL in available_baseline_methods()


def test_baseline_correct_unknown_method(uvvis_csv):
    spec = ingest_csv(
        uvvis_csv,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    with pytest.raises(ValueError, match="unknown baseline method"):
        baseline_correct(spec, method="not-a-real-method")


def test_available_methods_always_include_polynomial():
    methods = available_baseline_methods()
    assert methods[0] == METHOD_POLYNOMIAL
    if has_pybaselines():
        assert METHOD_ASLS in methods
        assert METHOD_MPLS in methods
    else:
        assert METHOD_ASLS not in methods


@pytest.mark.skipif(not has_pybaselines(), reason="pybaselines not installed")
@pytest.mark.parametrize("method", [METHOD_ASLS, METHOD_MPLS])
def test_pybaselines_methods_reduce_continuum(uvvis_csv, method):
    spec = ingest_csv(
        uvvis_csv,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    ends = np.concatenate([spec.y[:30], spec.y[-30:]])
    continuum_before = float(np.mean(ends))

    corrected = baseline_correct(spec, method=method, lam=1e5, p=0.01)
    assert corrected.meta["baseline_method"] == method
    assert "baseline" in corrected.meta
    ends_after = np.concatenate([corrected.y[:30], corrected.y[-30:]])
    continuum_after = float(np.abs(np.mean(ends_after)))
    assert continuum_after < continuum_before or continuum_after < 0.15, (
        f"{method}: continuum not reduced: before={continuum_before}, after={continuum_after}"
    )
    peaks = find_peaks(corrected, prominence=0.15)
    xs = [p.x for p in peaks]
    assert any(abs(x - 280) <= 15 for x in xs), f"{method} lost ~280: {xs}"
    assert any(abs(x - 350) <= 20 for x in xs), f"{method} lost ~350: {xs}"


def test_pybaselines_missing_raises_clear_import_error(uvvis_csv, monkeypatch):
    """Simulate missing optional dep → clear ImportError for asls/mpls."""
    import spectrum_core.baseline as bl

    held = {
        key: sys.modules.pop(key)
        for key in list(sys.modules)
        if key == "pybaselines" or key.startswith("pybaselines.")
    }

    class _Blocker:
        def find_spec(self, fullname, path, target=None):  # noqa: ARG002
            if fullname == "pybaselines" or fullname.startswith("pybaselines."):
                raise ModuleNotFoundError("No module named 'pybaselines'")
            return None

    blocker = _Blocker()
    monkeypatch.setattr(sys, "meta_path", [blocker, *sys.meta_path])

    try:
        assert bl.has_pybaselines() is False
        spec = ingest_csv(
            uvvis_csv,
            x_col="wavelength_nm",
            y_col="absorbance",
            x_unit="nm",
            y_unit="A",
        )
        with pytest.raises(ImportError, match=r"\[baselines\]"):
            baseline_correct(spec, method=METHOD_ASLS)
    finally:
        sys.modules.update(held)
