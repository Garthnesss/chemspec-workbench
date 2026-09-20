"""LabRF threshold event log + streaming frame generator (no UI / no sleep)."""

from datetime import datetime, timezone

import numpy as np
import pytest

from labrf.backend import MockIqSource
from labrf.events import ThresholdEventLog, evaluate_threshold
from labrf.fft_spectrum import iq_to_spectrum
from labrf.iq import generate_synthetic_iq
from labrf.stream import (
    MockStreamGenerator,
    format_labrf_provenance,
    format_stream_status,
)
from spectrum_core import find_peaks
from spectrum_core.spectrum import Spectrum


def _tone_spectrum(*, noise_std: float = 0.01, seed: int = 1) -> Spectrum:
    center = 98e6
    sr = 2.048e6
    iq, meta = generate_synthetic_iq(
        n_samples=2048,
        sample_rate=sr,
        center_freq=center,
        tones_hz=(center - 0.2e6, center + 0.3e6),
        tone_amps=(1.0, 0.8),
        noise_std=noise_std,
        seed=seed,
    )
    return iq_to_spectrum(
        iq,
        sample_rate=meta["sample_rate"],
        center_freq=meta["center_freq"],
        x_unit="MHz",
        y_unit="dB",
    )


def test_evaluate_threshold_max_bin_triggers():
    spec = _tone_spectrum()
    max_level = float(np.nanmax(spec.y))
    # Threshold below max → at least one max_bin event
    events = evaluate_threshold(
        spec,
        threshold_db=max_level - 1.0,
        peaks=None,
        now=datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc),
        use_peaks=False,
        use_max_bin=True,
    )
    assert len(events) == 1
    assert events[0].kind == "max_bin"
    assert events[0].level > max_level - 1.0
    assert events[0].timestamp.startswith("2026-09-19T12:00:00")


def test_evaluate_threshold_no_trigger_when_below():
    spec = _tone_spectrum()
    max_level = float(np.nanmax(spec.y))
    events = evaluate_threshold(
        spec,
        threshold_db=max_level + 50.0,
        peaks=find_peaks(spec, prominence=5.0),
        use_peaks=True,
        use_max_bin=True,
    )
    assert events == []


def test_evaluate_threshold_peak_kind():
    spec = _tone_spectrum()
    peaks = find_peaks(spec, prominence=5.0)
    assert peaks, "expected detectable tones"
    thr = max(p.y for p in peaks) - 0.5
    events = evaluate_threshold(
        spec,
        threshold_db=thr,
        peaks=peaks,
        use_peaks=True,
        use_max_bin=False,
    )
    assert events
    assert all(e.kind == "peak" for e in events)
    assert all(e.level > thr for e in events)


def test_event_log_append_clear_csv():
    log = ThresholdEventLog(threshold_db=-100.0)  # very low → always fire
    spec = _tone_spectrum()
    peaks = find_peaks(spec, prominence=5.0)
    new = log.check(spec, peaks)
    assert len(new) >= 1
    assert len(log) == len(new)
    csv_text = log.to_csv()
    assert "timestamp,freq,level,kind" in csv_text
    assert "max_bin" in csv_text or "peak" in csv_text
    log.clear()
    assert len(log) == 0
    assert log.to_csv().strip().endswith("y_unit") or "timestamp" in log.to_csv()


def test_event_log_set_threshold():
    log = ThresholdEventLog(threshold_db=0.0)
    log.set_threshold(-12.5)
    assert log.threshold_db == pytest.approx(-12.5)


def test_stream_generator_successive_frames_differ():
    src = MockIqSource(center_freq=98e6, sample_rate=2.048e6, seed=10)
    gen = MockStreamGenerator(source=src, n_fft=512, noise_jitter=0.02)
    f0 = gen.next_frame()
    f1 = gen.next_frame()
    f2 = gen.next_frame()
    assert f0.frame_index == 0
    assert f1.frame_index == 1
    assert f2.frame_index == 2
    assert f0.source_kind == "mock"
    # Spectra should not be identical (noise/tone jitter + seed step)
    assert not np.allclose(f0.spectrum.y, f1.spectrum.y)
    assert not np.allclose(f1.spectrum.y, f2.spectrum.y)
    assert f0.center_hz == pytest.approx(98e6)
    assert f0.sample_rate == pytest.approx(2.048e6)


def test_stream_generator_frame_count_and_reset():
    src = MockIqSource(seed=3)
    gen = MockStreamGenerator(source=src, n_fft=256, noise_jitter=0.0, tone_amp_jitter=0.0)
    for i in range(5):
        fr = gen.next_frame()
        assert fr.frame_index == i
        assert fr.spectrum.meta.get("streaming") is True
    gen.reset()
    assert gen.frame_index == 0
    assert gen.next_frame().frame_index == 0


def test_stream_plus_threshold_pipeline():
    """Streaming frames feed the event log without any UI timer."""
    src = MockIqSource(seed=99)
    gen = MockStreamGenerator(source=src, n_fft=1024)
    log = ThresholdEventLog(threshold_db=-200.0)  # always exceed
    for _ in range(4):
        frame = gen.next_frame()
        peaks = find_peaks(frame.spectrum, prominence=3.0)
        log.check(frame.spectrum, peaks)
    assert len(log) >= 4
    assert gen.frame_index == 4


def test_format_labrf_provenance():
    line = format_labrf_provenance(
        source_kind="mock",
        center_hz=98e6,
        sample_rate=2.048e6,
        frames=12,
        streaming=True,
        peak_count=3,
        threshold_db=-10.0,
        event_count=2,
    )
    assert "source=mock" in line
    assert "center=98.0000 MHz" in line
    assert "frames=12" in line
    assert "mode=streaming" in line
    assert "threshold=-10.0 dB" in line
    assert "events=2" in line


def test_event_log_maxlen_drops_oldest():
    log = ThresholdEventLog(threshold_db=-200.0, maxlen=5)
    spec = _tone_spectrum()
    for _ in range(8):
        log.check(spec, peaks=None)
    assert len(log) == 5
    # Uncapped still allowed
    log2 = ThresholdEventLog(threshold_db=-200.0, maxlen=None)
    for _ in range(3):
        log2.check(spec, peaks=None)
    assert len(log2) == 3


def test_event_log_rejects_bad_maxlen():
    with pytest.raises(ValueError, match="maxlen"):
        ThresholdEventLog(maxlen=0)


def test_format_stream_status_mock_and_fixture():
    mock_line = format_stream_status(
        source_kind="mock",
        frame_index=3,
        waterfall_frames=10,
        event_count=2,
    )
    assert "synthetic mock IQ" in mock_line
    assert "frame 3" in mock_line
    assert "receive-only demo" in mock_line
    assert "waterfall reset" not in mock_line

    fix_line = format_stream_status(
        source_kind="fixture",
        frame_index=1,
        waterfall_frames=4,
        event_count=0,
        axis_reset=True,
    )
    assert "synthetic fixture IQ" in fix_line
    assert "waterfall reset (retune)" in fix_line
    assert "receive-only demo" in fix_line
