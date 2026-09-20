"""LabRF mock IQ → FFT power spectrum (no hardware)."""

import numpy as np
import pytest

from labrf.fft_spectrum import iq_to_spectrum
from labrf.iq import (
    DEFAULT_IQ_FIXTURE,
    ensure_default_fixture,
    generate_synthetic_iq,
    load_iq_fixture,
)
from spectrum_core import find_peaks


def test_generate_synthetic_iq_complex():
    iq, meta = generate_synthetic_iq(n_samples=1024, seed=1)
    assert iq.dtype == np.complex128
    assert len(iq) == 1024
    assert meta["synthetic"] is True
    assert meta["sample_rate"] > 0


def test_iq_to_spectrum_mhz_db_and_tone_peaks():
    center = 98e6
    sr = 2.048e6
    tones = (center - 0.25e6, center + 0.4e6)
    iq, meta = generate_synthetic_iq(
        n_samples=4096,
        sample_rate=sr,
        center_freq=center,
        tones_hz=tones,
        tone_amps=(1.0, 0.8),
        noise_std=0.01,
        seed=7,
    )
    spec = iq_to_spectrum(
        iq,
        sample_rate=meta["sample_rate"],
        center_freq=meta["center_freq"],
        window="hann",
        x_unit="MHz",
        y_unit="dB",
    )
    assert spec.x_unit == "MHz"
    assert spec.y_unit == "dB"
    assert len(spec) == 4096
    # Axis spans roughly center ± sample_rate/2
    assert spec.x.min() < center / 1e6 < spec.x.max()
    peaks = find_peaks(spec, prominence=5.0)
    peak_mhz = [p.x for p in peaks[:10]]
    for tone in tones:
        target = tone / 1e6
        assert any(abs(x - target) < 0.05 for x in peak_mhz), (
            f"missing tone near {target} MHz; peaks={peak_mhz}"
        )


def test_iq_to_spectrum_hz_intensity():
    iq, meta = generate_synthetic_iq(n_samples=512, seed=2)
    spec = iq_to_spectrum(
        iq,
        sample_rate=meta["sample_rate"],
        center_freq=meta["center_freq"],
        x_unit="Hz",
        y_unit="intensity",
    )
    assert spec.x_unit == "Hz"
    assert spec.y_unit == "intensity"
    assert np.all(spec.y >= 0)


def test_fixture_roundtrip(tmp_path):
    ensure_default_fixture()
    assert DEFAULT_IQ_FIXTURE.is_file()
    iq, meta = load_iq_fixture(DEFAULT_IQ_FIXTURE)
    assert np.iscomplexobj(iq)
    assert "sample_rate" in meta and "center_freq" in meta
    spec = iq_to_spectrum(
        iq[:2048],
        sample_rate=meta["sample_rate"],
        center_freq=meta["center_freq"],
    )
    assert spec.x_unit == "MHz"
    assert len(spec) == 2048


def test_rejects_real_iq():
    with pytest.raises(ValueError, match="complex"):
        iq_to_spectrum(
            np.ones(64),
            sample_rate=1e6,
            center_freq=1e8,
        )
