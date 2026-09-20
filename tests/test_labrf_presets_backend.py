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
