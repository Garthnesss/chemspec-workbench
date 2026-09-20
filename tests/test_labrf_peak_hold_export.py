"""LabRF peak-hold / max-hold + PNG export (mock path, no hardware)."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pytest

from labrf.export_png import export_spectrum_png, export_waterfall_png
from labrf.fft_spectrum import iq_to_spectrum
from labrf.iq import generate_synthetic_iq
from labrf.peak_hold import PeakHoldTracker
from labrf.waterfall import WaterfallBuffer
from spectrum_core import find_peaks
from spectrum_core.spectrum import Spectrum


def _tone_spectrum(*, seed: int = 1, noise_std: float = 0.02) -> Spectrum:
    center = 98e6
    sr = 2.048e6
    iq, meta = generate_synthetic_iq(
        n_samples=1024,
        sample_rate=sr,
        center_freq=center,
        tones_hz=(center - 0.2e6,),
        tone_amps=(1.0,),
        noise_std=noise_std,
        seed=seed,
    )
    return iq_to_spectrum(
        iq,
        sample_rate=meta["sample_rate"],
        center_freq=meta["center_freq"],
        x_unit="MHz",
        y_unit="dB",
        title="Mock RF power spectrum (synthetic)",
        meta={"synthetic": True},
    )


def test_peak_hold_disabled_returns_none():
    tracker = PeakHoldTracker(enabled=False)
    spec = _tone_spectrum(seed=1)
    assert tracker.update(spec) is None
    assert tracker.held is None
    assert tracker.n_updates == 0


def test_peak_hold_accumulates_max_per_bin():
    tracker = PeakHoldTracker(enabled=True)
    a = _tone_spectrum(seed=1, noise_std=0.05)
    b = _tone_spectrum(seed=2, noise_std=0.05)
    # Force a higher bin on b so max is strictly above a somewhere
    b = b.with_y(b.y + 3.0)
    held_a = tracker.update(a)
    assert held_a is not None
    assert np.allclose(held_a.y, a.y)
    held_b = tracker.update(b)
    assert held_b is not None
    assert tracker.n_updates == 2
    assert np.all(held_b.y >= a.y - 1e-12)
    assert np.all(held_b.y >= b.y - 1e-12)
    assert np.allclose(held_b.y, np.maximum(a.y, b.y))
    assert held_b.meta.get("peak_hold") is True
    assert held_b.meta.get("max_hold") is True
    assert "peak-hold" in held_b.title.lower() or "max-hold" in held_b.title.lower()


def test_peak_hold_resets_on_axis_change():
    tracker = PeakHoldTracker(enabled=True)
    a = _tone_spectrum(seed=1)
    tracker.update(a)
    # Shift frequency axis (retune)
    retuned = Spectrum(
        x=a.x + 1.0,
        y=a.y - 20.0,
        x_unit=a.x_unit,
        y_unit=a.y_unit,
        title=a.title,
        meta=dict(a.meta),
    )
    held = tracker.update(retuned)
    assert held is not None
    assert tracker.n_updates == 1
    assert np.allclose(held.x, retuned.x)
    assert np.allclose(held.y, retuned.y)


def test_peak_hold_clear():
    tracker = PeakHoldTracker(enabled=True)
    tracker.update(_tone_spectrum(seed=3))
    assert tracker.held is not None
    tracker.clear()
    assert tracker.held is None
    assert tracker.n_updates == 0


def test_export_spectrum_png_writes_file(tmp_path: Path):
    spec = _tone_spectrum(seed=4)
    peaks = find_peaks(spec, prominence=5.0)
    out = tmp_path / "spectrum.png"
    path = export_spectrum_png(
        spec,
        out,
        peaks=peaks,
        threshold_db=-40.0,
        honesty_note="Educational / mock IQ — receive-only; not hardware-verified",
    )
    assert path == out
    assert out.is_file()
    assert out.stat().st_size > 500
    # PNG magic
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_export_spectrum_png_with_peak_hold_bytesio():
    tracker = PeakHoldTracker(enabled=True)
    a = _tone_spectrum(seed=5)
    b = _tone_spectrum(seed=6).with_y(_tone_spectrum(seed=6).y + 2.0)
    tracker.update(a)
    held = tracker.update(b)
    buf = io.BytesIO()
    result = export_spectrum_png(a, buf, peak_hold=held)
    assert result is None
    data = buf.getvalue()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 500


def test_export_waterfall_png(tmp_path: Path):
    wf = WaterfallBuffer(maxlen=8)
    for seed in range(4):
        wf.push(_tone_spectrum(seed=seed))
    out = tmp_path / "waterfall.png"
    path = export_waterfall_png(wf, out, title="LabRF waterfall (mock / educational)")
    assert path == out
    assert out.is_file()
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_export_waterfall_png_empty_raises():
    wf = WaterfallBuffer(maxlen=4)
    with pytest.raises(ValueError, match="empty"):
        export_waterfall_png(wf, io.BytesIO())


def test_package_exports():
    import labrf

    assert hasattr(labrf, "PeakHoldTracker")
    assert hasattr(labrf, "export_spectrum_png")
    assert hasattr(labrf, "export_waterfall_png")
