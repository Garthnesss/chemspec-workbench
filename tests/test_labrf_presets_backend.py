"""LabRF presets + mock backend + optional RTL import guard (no hardware)."""

import pytest

from labrf.backend import MockIqSource, open_rtlsdr_source
from labrf.fft_spectrum import iq_to_spectrum
from labrf.presets import PRESETS_DISCLAIMER, load_presets
from labrf.rtlsdr_adapter import _MISSING_MSG
from labrf.waterfall import WaterfallBuffer


def test_presets_load_and_disclaimer():
    pack = load_presets()
    assert pack.presets
    assert "not regulatory advice" in pack.disclaimer.lower()
    assert "not regulatory advice" in PRESETS_DISCLAIMER.lower()
    ids = {p.id for p in pack.presets}
    assert "fm_broadcast" in ids
    assert "ism_24" in ids
    fm = pack.by_id("fm_broadcast")
    assert fm.center_hz == pytest.approx(98e6)
    assert fm.sample_rate_hz > 0


def test_mock_backend_no_hardware():
    src = MockIqSource(center_freq=98e6, sample_rate=2.048e6, seed=3)
    iq = src.read_samples(1024)
    assert len(iq) == 1024
    assert iq.dtype.kind == "c"
    spec = iq_to_spectrum(
        iq, sample_rate=src.sample_rate, center_freq=src.center_freq
    )
    assert spec.y_unit == "dB"


def test_waterfall_buffer_matrix_and_stack():
    src = MockIqSource(seed=5)
    buf = WaterfallBuffer(maxlen=5)
    for _ in range(3):
        iq = src.read_samples(512)
        spec = iq_to_spectrum(
            iq, sample_rate=src.sample_rate, center_freq=src.center_freq
        )
        buf.push(spec)
    assert len(buf) == 3
    x, z = buf.as_matrix()
    assert z.shape == (3, 512)
    assert len(x) == 512
    stacked = buf.as_stacked()
    assert len(stacked) == 3
    assert stacked[1].meta["stack_index"] == 1


def test_rtlsdr_import_error_is_clear():
    """Without pyrtlsdr installed, open_rtlsdr_source must fail clearly."""
    try:
        import rtlsdr  # noqa: F401

        pytest.skip("pyrtlsdr installed in this env — skip missing-extra check")
    except ImportError:
        pass
    with pytest.raises(ImportError, match="pip install") as ei:
        open_rtlsdr_source()
    assert "labrf" in str(ei.value).lower() or "rtlsdr" in str(ei.value).lower()
    assert "MockIqSource" in _MISSING_MSG or "mock" in _MISSING_MSG.lower()


def test_configure_noop_does_not_advance_seed():
    src = MockIqSource(center_freq=98e6, sample_rate=2.048e6, seed=10)
    assert src.configure(center_freq=98e6, sample_rate=2.048e6) is False
    assert src.seed == 10
    assert src.configure(center_freq=100e6, sample_rate=2.048e6) is True
    assert src.seed == 11
    assert src.center_freq == pytest.approx(100e6)


def test_fixture_ring_read_vectorized_and_loops(tmp_path):
    import numpy as np
    from labrf.iq import save_iq_fixture

    iq = (np.arange(100) + 1j * np.arange(100)).astype(np.complex64)
    path = tmp_path / "tiny_iq.npz"
    save_iq_fixture(path, iq, sample_rate=1e6, center_freq=50e6, note="test")
    src = MockIqSource(fixture_path=str(path))
    a = src.read_samples(80)
    b = src.read_samples(80)
    assert len(a) == 80 and len(b) == 80
    # Continuity across the ring boundary (cursor advanced)
    full = np.concatenate([a, b])
    expected = np.tile(iq.astype(np.complex128), 2)[:160]
    assert np.allclose(full, expected)


def test_waterfall_resets_on_frequency_axis_change():
    import numpy as np
    from spectrum_core.spectrum import Spectrum

    buf = WaterfallBuffer(maxlen=8)
    x0 = np.linspace(97.0, 99.0, 64)
    y = np.zeros(64)
    s0 = Spectrum(x=x0, y=y, x_unit="MHz", y_unit="dB", title="a")
    assert buf.push(s0) is False
    assert len(buf) == 1
    # Same axis → no reset
    s1 = Spectrum(x=x0.copy(), y=y + 1, x_unit="MHz", y_unit="dB", title="b")
    assert buf.push(s1) is False
    assert len(buf) == 2
    # Retune shifts x → auto-clear then keep newest only
    x1 = np.linspace(144.0, 146.0, 64)
    s2 = Spectrum(x=x1, y=y + 2, x_unit="MHz", y_unit="dB", title="c")
    assert buf.push(s2) is True
    assert len(buf) == 1
    x_out, z = buf.as_matrix()
    assert np.allclose(x_out, x1)
    assert z.shape == (1, 64)
