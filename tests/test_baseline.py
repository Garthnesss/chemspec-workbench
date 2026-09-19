"""Baseline reduces continuum without deleting peaks entirely."""

import numpy as np

from spectrum_core import baseline_polynomial, find_peaks, ingest_csv


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
