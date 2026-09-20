"""Synthetic complex IQ generation and fixture load (no dongle required)."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np

# Default fixture lives next to ChemSpec fixtures.
_REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IQ_FIXTURE = _REPO_ROOT / "fixtures" / "labrf" / "mock_iq.npz"


def generate_synthetic_iq(
    n_samples: int = 4096,
    *,
    sample_rate: float = 2.048e6,
    center_freq: float = 98e6,
    tones_hz: Sequence[float] | None = None,
    tone_amps: Sequence[float] | None = None,
    noise_std: float = 0.05,
    seed: int | None = 42,
) -> tuple[np.ndarray, dict]:
    """Generate complex baseband IQ with optional CW tones + noise.

    ``tones_hz`` are absolute RF frequencies (Hz). Each tone is mixed to
    baseband relative to ``center_freq``. Returns ``(iq, meta)`` where ``iq``
    is ``complex128`` length ``n_samples``.

    This is **synthetic** teaching data — not a live capture.
    """
    if n_samples < 8:
        raise ValueError("n_samples must be >= 8")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")

    if tones_hz is None:
        # Default: two tones inside an FM-ish educational span
        tones_hz = (center_freq - 0.3e6, center_freq + 0.5e6)
    tones = [float(t) for t in tones_hz]
    if tone_amps is None:
        amps = [1.0] * len(tones)
    else:
        amps = [float(a) for a in tone_amps]
        if len(amps) != len(tones):
            raise ValueError("tone_amps length must match tones_hz")

    rng = np.random.default_rng(seed)
    t = np.arange(n_samples, dtype=float) / float(sample_rate)
    iq = np.zeros(n_samples, dtype=np.complex128)
    for tone, amp in zip(tones, amps):
        f_bb = tone - float(center_freq)
        iq += amp * np.exp(2j * np.pi * f_bb * t)

    if noise_std > 0:
        noise = rng.normal(0.0, noise_std, n_samples) + 1j * rng.normal(
            0.0, noise_std, n_samples
        )
        iq += noise

    meta = {
        "synthetic": True,
        "sample_rate": float(sample_rate),
        "center_freq": float(center_freq),
        "tones_hz": tones,
        "tone_amps": amps,
        "noise_std": float(noise_std),
        "seed": seed,
        "n_samples": int(n_samples),
        "source": "labrf.generate_synthetic_iq",
    }
    return iq, meta


def save_iq_fixture(
    path: str | Path,
    iq: np.ndarray,
    *,
    sample_rate: float,
    center_freq: float,
    **extra_meta: object,
) -> Path:
    """Write complex IQ + metadata to a ``.npz`` fixture."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    iq = np.asarray(iq)
    if not np.iscomplexobj(iq):
        raise ValueError("iq must be complex")
    meta = {
        "sample_rate": float(sample_rate),
        "center_freq": float(center_freq),
        "synthetic": True,
        **{k: v for k, v in extra_meta.items()},
    }
    # Store meta keys as arrays for np.savez compatibility
    payload: dict[str, object] = {"iq": iq.astype(np.complex64)}
    for k, v in meta.items():
        if isinstance(v, (list, tuple)):
            payload[f"meta_{k}"] = np.asarray(v)
        elif isinstance(v, (bool, np.bool_)):
            payload[f"meta_{k}"] = np.asarray(bool(v))
        elif isinstance(v, (int, float, np.integer, np.floating)):
            payload[f"meta_{k}"] = np.asarray(v)
        else:
            payload[f"meta_{k}"] = np.asarray(str(v))
    np.savez_compressed(path, **payload)
    return path


def load_iq_fixture(path: str | Path | None = None) -> tuple[np.ndarray, dict]:
    """Load complex IQ fixture (``.npz``). Defaults to ``fixtures/labrf/mock_iq.npz``.

    Returns ``(iq, meta)`` with at least ``sample_rate`` and ``center_freq``.
    """
    path = Path(path) if path is not None else DEFAULT_IQ_FIXTURE
    if not path.is_file():
        raise FileNotFoundError(
            f"IQ fixture not found: {path}. Generate with labrf.iq.save_iq_fixture "
            "or run tests that create fixtures/labrf/mock_iq.npz"
        )
    data = np.load(path, allow_pickle=False)
    if "iq" not in data:
        raise ValueError(f"fixture {path} missing 'iq' array")
    iq = np.asarray(data["iq"])
    if not np.iscomplexobj(iq):
        # Allow real/imag split storage
        if "iq_real" in data and "iq_imag" in data:
            iq = np.asarray(data["iq_real"]) + 1j * np.asarray(data["iq_imag"])
        else:
            raise ValueError(f"fixture {path} iq is not complex")

    meta: dict = {"path": str(path), "synthetic": True}
    for key in data.files:
        if key.startswith("meta_"):
            raw = data[key]
            name = key[len("meta_") :]
            if raw.shape == ():
                val = raw.item()
            else:
                val = raw.tolist()
            meta[name] = val

    if "sample_rate" not in meta or "center_freq" not in meta:
        raise ValueError(
            f"fixture {path} must include meta_sample_rate and meta_center_freq"
        )
    meta["sample_rate"] = float(meta["sample_rate"])
    meta["center_freq"] = float(meta["center_freq"])
    return iq.astype(np.complex128), meta


def ensure_default_fixture(
    path: str | Path | None = None,
    *,
    overwrite: bool = False,
) -> Path:
    """Create the default mock IQ fixture if missing (or if ``overwrite``)."""
    path = Path(path) if path is not None else DEFAULT_IQ_FIXTURE
    if path.is_file() and not overwrite:
        return path
    iq, meta = generate_synthetic_iq(
        n_samples=4096,
        sample_rate=2.048e6,
        center_freq=98e6,
        tones_hz=(97.7e6, 98.5e6),
        tone_amps=(1.0, 0.7),
        noise_std=0.04,
        seed=42,
    )
    return save_iq_fixture(
        path,
        iq,
        sample_rate=meta["sample_rate"],
        center_freq=meta["center_freq"],
        tones_hz=meta["tones_hz"],
        note="synthetic mock IQ for LabRF CI / UI — not a live capture",
    )
