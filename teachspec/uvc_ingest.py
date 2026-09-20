"""UVC (USB camera) ingest interface — Phase-0 stub only.

Docs lock USB camera (UVC) as TeachSpec v1 primary sensor. This module defines
the **ingest contract** and a placeholder backend that raises
``NotImplementedError``. Live camera capture (OpenCV / OS UVC APIs) is
**Planned** and intentionally **not** a package dependency yet.

Use ``teachspec.generate_mock_frame`` for demos and pytest. See
``docs/family/teachspec/`` (SPEC, SAFETY, BOM_v0) and ``teachspec/README.md``.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np

from teachspec.optical import OpticalLiveFrame


@runtime_checkable
class OpticalFrameSource(Protocol):
    """Thin protocol for optical frame backends (mock or future UVC).

    Implementations must return an ``OpticalLiveFrame`` (1-D intensity). Live
    UVC backends (when Implemented) should extract a single row/column from
    the camera image before wrapping — see ``extract_row``.
    """

    def read_frame(self) -> OpticalLiveFrame:
        """Return one 1-D intensity frame (mock or live)."""
        ...

    def close(self) -> None:
        """Release any hardware / OS resources (no-op for mocks)."""
        ...


def extract_row(image: np.ndarray, *, row: int | None = None) -> np.ndarray:
    """Extract a 1-D intensity row from a 2-D (or HxWxC) image array.

    Pure NumPy helper for a future UVC backend — **no** OpenCV required.
    Defaults to the vertical mid-line (typical teaching-spectrometer slit
    projection). Does not claim wavelength calibration.
    """
    arr = np.asarray(image)
    if arr.ndim == 3:
        # Average colour channels → relative intensity (not calibrated RGB→lm)
        arr = arr.astype(float).mean(axis=2)
    if arr.ndim != 2:
        raise ValueError("image must be 2-D (H×W) or 3-D (H×W×C)")
    if arr.size == 0:
        raise ValueError("image must be non-empty")
    h, _w = arr.shape
    r = int(h // 2) if row is None else int(row)
    if r < 0 or r >= h:
        raise ValueError(f"row index {r} out of range for height {h}")
    return np.asarray(arr[r, :], dtype=float)


class UvcIngestStub:
    """Placeholder UVC backend — raises until a live driver is Implemented.

    Kept importable so docs, type checkers, and future OpenCV extras can
    target a stable name without pulling camera libraries into CI.
    """

    def __init__(
        self,
        *,
        device_index: int = 0,
        row: int | None = None,
    ) -> None:
        self.device_index = int(device_index)
        self.row = row

    def read_frame(self) -> OpticalLiveFrame:
        raise NotImplementedError(
            "Live UVC ingest is not Implemented in TeachSpec Phase-0. "
            "Use teachspec.generate_mock_frame() for synthetic frames. "
            "Optional OpenCV/UVC capture is Planned (see teachspec/README.md "
            "and docs/family/teachspec/); no camera dependency is required now."
        )

    def close(self) -> None:
        """No-op — no device handle exists on the stub."""
        return None


__all__ = [
    "OpticalFrameSource",
    "UvcIngestStub",
    "extract_row",
]
