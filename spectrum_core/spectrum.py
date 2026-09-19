"""Spectrum dataclass: x/y arrays plus unit and metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np

XUnit = Literal["nm", "cm-1"]
YUnit = Literal["A", "percent_T", "intensity"]


@dataclass
class Spectrum:
    """A single 1-D spectrum with axis units and optional metadata."""

    x: np.ndarray
    y: np.ndarray
    x_unit: XUnit = "nm"
    y_unit: YUnit = "intensity"
    title: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.x = np.asarray(self.x, dtype=float)
        self.y = np.asarray(self.y, dtype=float)
        if self.x.ndim != 1 or self.y.ndim != 1:
            raise ValueError("x and y must be 1-D arrays")
        if len(self.x) != len(self.y):
            raise ValueError(
                f"x and y length mismatch: {len(self.x)} vs {len(self.y)}"
            )
        if len(self.x) == 0:
            raise ValueError("spectrum must have at least one point")
        if self.x_unit not in ("nm", "cm-1"):
            raise ValueError(f"unsupported x_unit: {self.x_unit!r}")
        if self.y_unit not in ("A", "percent_T", "intensity"):
            raise ValueError(f"unsupported y_unit: {self.y_unit!r}")

    def __len__(self) -> int:
        return len(self.x)

    def copy(self) -> Spectrum:
        return Spectrum(
            x=self.x.copy(),
            y=self.y.copy(),
            x_unit=self.x_unit,
            y_unit=self.y_unit,
            title=self.title,
            meta=dict(self.meta),
        )

    def with_y(self, y: np.ndarray, *, title: str | None = None) -> Spectrum:
        """Return a new Spectrum sharing x/units, with a new y array."""
        return Spectrum(
            x=self.x.copy(),
            y=np.asarray(y, dtype=float),
            x_unit=self.x_unit,
            y_unit=self.y_unit,
            title=self.title if title is None else title,
            meta=dict(self.meta),
        )
