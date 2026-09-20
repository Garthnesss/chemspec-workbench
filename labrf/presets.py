"""Educational frequency presets (JSON). Not regulatory advice."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PRESETS_PATH = Path(__file__).resolve().parent / "data" / "educational.json"

PRESETS_DISCLAIMER = (
    "Educational presets only — not regulatory advice. "
    "LabRF Monitor is receive-only EMI / situational awareness; "
    "it does not identify chemicals and does not claim compliance testing."
)


@dataclass(frozen=True)
class RfPreset:
    """One educational RF tuning preset."""

    id: str
    name: str
    center_hz: float
    span_hz: float
    sample_rate_hz: float
    notes: str = ""

    @property
    def center_mhz(self) -> float:
        return self.center_hz / 1e6


@dataclass(frozen=True)
class PresetPack:
    disclaimer: str
    presets: list[RfPreset]

    def by_id(self, preset_id: str) -> RfPreset:
        for p in self.presets:
            if p.id == preset_id:
                return p
        raise KeyError(f"unknown preset id: {preset_id!r}")

    def as_choices(self) -> list[tuple[str, str]]:
        """NiceGUI-friendly ``(label, value)`` pairs."""
        return [(p.name, p.id) for p in self.presets]


def load_presets(path: str | Path | None = None) -> PresetPack:
    """Load educational presets JSON (default: packaged ``educational.json``)."""
    path = Path(path) if path is not None else _PRESETS_PATH
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    disclaimer = str(raw.get("disclaimer") or PRESETS_DISCLAIMER)
    presets: list[RfPreset] = []
    for item in raw.get("presets", []):
        presets.append(
            RfPreset(
                id=str(item["id"]),
                name=str(item["name"]),
                center_hz=float(item["center_hz"]),
                span_hz=float(item.get("span_hz") or item.get("sample_rate_hz")),
                sample_rate_hz=float(
                    item.get("sample_rate_hz") or item.get("span_hz")
                ),
                notes=str(item.get("notes") or ""),
            )
        )
    if not presets:
        raise ValueError(f"no presets found in {path}")
    return PresetPack(disclaimer=disclaimer, presets=presets)
