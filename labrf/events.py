"""Threshold event log for RF power spectra (receive-only awareness)."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Sequence

import numpy as np

from spectrum_core.spectrum import Spectrum
from spectrum_core.peaks import Peak


@dataclass(frozen=True)
class ThresholdEvent:
    """One timestamped threshold crossing (frequency + level)."""

    timestamp: str
    freq: float
    level: float
    kind: str  # "peak" | "max_bin"
    x_unit: str = "MHz"
    y_unit: str = "dB"

    def as_row(self) -> dict[str, object]:
        return {
            "timestamp": self.timestamp,
            "freq": round(self.freq, 6),
            "level": round(self.level, 3),
            "kind": self.kind,
            "x_unit": self.x_unit,
            "y_unit": self.y_unit,
        }


def _iso_now(now: datetime | None = None) -> str:
    dt = now if now is not None else datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def evaluate_threshold(
    spectrum: Spectrum,
    threshold_db: float,
    *,
    peaks: Sequence[Peak] | None = None,
    now: datetime | None = None,
    use_peaks: bool = True,
    use_max_bin: bool = True,
) -> list[ThresholdEvent]:
    """Return events when peak and/or max-bin level exceeds ``threshold_db``.

    Pure function — no UI, no sleep. Levels are compared in the spectrum's
    ``y`` units (expected dB for LabRF). Frequency uses spectrum ``x``.
    """
    if spectrum.y.size == 0:
        return []

    ts = _iso_now(now)
    events: list[ThresholdEvent] = []
    xu = spectrum.x_unit
    yu = spectrum.y_unit

    if use_max_bin:
        idx = int(np.nanargmax(spectrum.y))
        level = float(spectrum.y[idx])
        if level > float(threshold_db):
            events.append(
                ThresholdEvent(
                    timestamp=ts,
                    freq=float(spectrum.x[idx]),
                    level=level,
                    kind="max_bin",
                    x_unit=xu,
                    y_unit=yu,
                )
            )

    if use_peaks and peaks:
        for p in peaks:
            if float(p.y) > float(threshold_db):
                events.append(
                    ThresholdEvent(
                        timestamp=ts,
                        freq=float(p.x),
                        level=float(p.y),
                        kind="peak",
                        x_unit=xu,
                        y_unit=yu,
                    )
                )

    return events


@dataclass
class ThresholdEventLog:
    """Append-only event log with optional CSV export."""

    threshold_db: float = -20.0
    events: list[ThresholdEvent] = field(default_factory=list)
    use_peaks: bool = True
    use_max_bin: bool = True
    # Deduplicate same-kind events within a frame when levels already logged
    # at identical freq — keep simple: append all evaluate results.

    def set_threshold(self, threshold_db: float) -> None:
        self.threshold_db = float(threshold_db)

    def clear(self) -> None:
        self.events.clear()

    def __len__(self) -> int:
        return len(self.events)

    def check(
        self,
        spectrum: Spectrum,
        peaks: Sequence[Peak] | None = None,
        *,
        now: datetime | None = None,
    ) -> list[ThresholdEvent]:
        """Evaluate spectrum against threshold and append any new events."""
        new = evaluate_threshold(
            spectrum,
            self.threshold_db,
            peaks=peaks,
            now=now,
            use_peaks=self.use_peaks,
            use_max_bin=self.use_max_bin,
        )
        self.events.extend(new)
        return new

    def rows(self) -> list[dict[str, object]]:
        return [e.as_row() for e in self.events]

    def to_csv(self) -> str:
        """Return CSV text (header + rows) suitable for download."""
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=["timestamp", "freq", "level", "kind", "x_unit", "y_unit"],
        )
        writer.writeheader()
        for row in self.rows():
            writer.writerow(row)
        return buf.getvalue()
