"""FID/NMR Phase-0: mock FID → FFT/phase → Spectrum (no magnet)."""

from __future__ import annotations

import numpy as np
import pytest

from spectrum_core import find_peaks
from spectrum_core.spectrum import Spectrum

from fidnmr import (
    FID,
    apodize_exp,
    fid_to_spectrum,
    generate_mock_fid,
    hz_to_ppm,
)
from fidnmr.mock_source import DEFAULT_TEACHING_PEAKS_PPM


def test_hz_to_ppm_roundtrip_inverse():
    obs = 400.0
    ref = 0.0
    freqs = np.array([0.0, 400.0, 800.0])  # → 0, 1, 2 ppm
    ppm = hz_to_ppm(freqs, obs_mhz=obs, ref_ppm=ref)
    np.testing.assert_allclose(ppm, [0.0, 1.0, 2.0])


def test_fid_rejects_real_signal():
    with pytest.raises(ValueError, match="complex"):
        FID(signal=np.ones(16), sw_hz=1000.0, obs_mhz=400.0)


def test_fid_rejects_bad_sw():
    z = np.ones(16, dtype=np.complex128)
    with pytest.raises(ValueError, match="sw_hz"):
        FID(signal=z, sw_hz=0.0, obs_mhz=400.0)


def test_mock_fid_to_spectrum_recovers_teaching_peaks():
    fid, truth = generate_mock_fid(
        npts=4096,
        sw_hz=8000.0,
        obs_mhz=400.0,
        peaks_ppm=DEFAULT_TEACHING_PEAKS_PPM,
        noise_std=0.0,
        seed=0,
    )
    spec = fid_to_spectrum(fid, lb_hz=0.5, phc0_deg=0.0, x_unit="ppm")
    assert spec.x_unit == "ppm"
    assert spec.y_unit == "intensity"
    assert spec.meta.get("synthetic") or fid.meta.get("synthetic")
    pick = Spectrum(
        x=spec.x, y=np.abs(spec.y), x_unit="ppm", y_unit="intensity"
    )
    peaks = find_peaks(pick, prominence=0.02)
    found = sorted(p.x for p in peaks)
    for expected in truth["peaks_ppm"]:
        assert any(abs(f - expected) < 0.15 for f in found), (
            f"missing peak near {expected} ppm; found={found}"
        )


def test_fid_to_spectrum_hz_axis():
    fid, truth = generate_mock_fid(
        npts=1024, peaks_ppm=(1.0,), amplitudes=(1.0,), noise_std=0.0
    )
    spec = fid_to_spectrum(fid, x_unit="Hz", lb_hz=0.0)
    assert spec.x_unit == "Hz"
    # Peak should land near (1.0 - ref) * obs_mhz
    expected_hz = truth["peak_freqs_hz"][0]
    pick = Spectrum(
        x=spec.x, y=np.abs(spec.y), x_unit="Hz", y_unit="intensity"
    )
    peaks = find_peaks(pick, prominence=0.02)
    assert peaks, "expected at least one peak"
    assert abs(peaks[0].x - expected_hz) < 5.0  # Hz tolerance on coarse grid


def test_phc0_180_negates_real_spectrum():
    """Causal FID lineshapes are already complex; 180° must negate real part."""
    fid, _ = generate_mock_fid(
        npts=2048, peaks_ppm=(2.0,), amplitudes=(1.0,), noise_std=0.0, ph0_deg=0.0
    )
    s0 = fid_to_spectrum(fid, phc0_deg=0.0, x_unit="ppm", real_only=True)
    s180 = fid_to_spectrum(fid, phc0_deg=180.0, x_unit="ppm", real_only=True)
    np.testing.assert_allclose(s180.y, -s0.y, atol=1e-8, rtol=0)
    s90 = fid_to_spectrum(fid, phc0_deg=90.0, x_unit="ppm", real_only=True)
    # 90° must change the real spectrum (not a no-op)
    assert not np.allclose(s90.y, s0.y, atol=1e-6)


def test_apodize_exp_does_not_mutate_input():
    fid, _ = generate_mock_fid(npts=256, noise_std=0.0)
    before = fid.signal.copy()
    out = apodize_exp(fid, lb_hz=5.0)
    np.testing.assert_array_equal(fid.signal, before)
    assert out is not fid
    assert np.max(np.abs(out.signal)) <= np.max(np.abs(before)) + 1e-12


def test_apodize_rejects_negative_lb():
    fid, _ = generate_mock_fid(npts=128, noise_std=0.0)
    with pytest.raises(ValueError, match="lb_hz"):
        apodize_exp(fid, lb_hz=-1.0)


def test_spectrum_accepts_ppm_unit():
    s = Spectrum(x=np.array([0.0, 1.0]), y=np.array([0.0, 1.0]), x_unit="ppm")
    assert s.x_unit == "ppm"


def test_generate_mock_rejects_empty_peaks():
    with pytest.raises(ValueError, match="non-empty"):
        generate_mock_fid(peaks_ppm=[])
