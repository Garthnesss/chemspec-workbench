"""UVC (USB camera) ingest — protocol, stub, and optional OpenCV backend.

Docs lock USB camera (UVC) as TeachSpec v1 primary sensor. This module defines:

* ``OpticalFrameSource`` — thin protocol for mock / live backends
* ``extract_row`` — pure-NumPy 2-D/HxWxC → 1-D intensity (no OpenCV)
* ``UvcIngestStub`` — explicit no-camera placeholder (``NotImplementedError``)
* ``UvcOpenCvSource`` — optional live capture via ``opencv-python-headless``
* ``open_uvc_source`` — factory that opens the OpenCV backend (never silent stub)

CI and default installs stay camera-free: OpenCV is the ``[teachspec]`` extra only.
Live frames are **intensity vs pixel** until the user applies
``teachspec.calibration`` — the camera alone is not wavelength-calibrated.
See ``docs/family/teachspec/`` (SPEC, SAFETY, BOM_v0) and ``teachspec/README.md``.

**Thread-safety:** ``UvcOpenCvSource`` is intended for **single-threaded** use.
Do not share one instance across threads without external locking.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import numpy as np

from teachspec.optical import OpticalLiveFrame

_OPENCV_MISSING_MSG = (
    "Live UVC OpenCV ingest requires the optional TeachSpec extra. Install with:\n"
    '  pip install -e ".[teachspec]"\n'
    "For camera-free demos use teachspec.generate_mock_frame() or "
    "teachspec.demo --mock (default). "
    "UvcIngestStub remains for explicit no-camera placeholders."
)


@runtime_checkable
class OpticalFrameSource(Protocol):
    """Thin protocol for optical frame backends (mock or live UVC).

    Implementations must return an ``OpticalLiveFrame`` (1-D intensity). Live
    UVC backends should extract a single row/column from the camera image
    before wrapping — see ``extract_row``.
    """

    def read_frame(self) -> OpticalLiveFrame:
        """Return one 1-D intensity frame (mock or live)."""
        ...

    def close(self) -> None:
        """Release any hardware / OS resources (no-op for mocks)."""
        ...


def extract_row(image: np.ndarray, *, row: int | None = None) -> np.ndarray:
    """Extract a 1-D intensity row from a 2-D (or HxWxC) image array.

    Pure NumPy helper for UVC backends — **no** OpenCV required.
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


def _import_cv2() -> Any:
    """Lazy-import OpenCV; raise a clear InstallError-style ImportError if missing."""
    try:
        import cv2  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch / missing-extra
        raise ImportError(_OPENCV_MISSING_MSG) from exc
    return cv2


class UvcIngestStub:
    """Explicit no-camera UVC placeholder — always raises on ``read_frame``.

    Kept importable for docs, type checkers, and demos that must not touch a
    camera. Prefer ``UvcOpenCvSource`` / ``open_uvc_source`` for live capture
    (optional ``[teachspec]`` extra), or ``generate_mock_frame`` for synthetic.
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
            "UvcIngestStub does not capture frames (explicit no-camera placeholder). "
            "For live UVC install the optional extra and use open_uvc_source() / "
            "UvcOpenCvSource (pip install -e \".[teachspec]\"). "
            "For synthetic demos use teachspec.generate_mock_frame() or "
            "teachspec.demo --mock. Live OpenCV path is Implemented as an optional extra."
        )

    def close(self) -> None:
        """No-op — no device handle exists on the stub."""
        return None


class UvcOpenCvSource:
    """Live UVC frame source via OpenCV ``VideoCapture`` (optional extra).

    Requires ``opencv-python-headless`` from the ``[teachspec]`` extra. Frames
    are returned as 1-D intensity (``extract_row`` on BGR grab). Metadata marks
    ``source=uvc_opencv`` and that the path is **not** wavelength-calibrated by
    the camera alone — apply ``teachspec.calibration`` separately.

    **Thread-safety:** single-threaded use only; do not share across threads
    without external synchronization.
    """

    def __init__(
        self,
        device_index: int = 0,
        row: int | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        cv2 = _import_cv2()
        self.device_index = int(device_index)
        self.row = row
        self.width = int(width) if width is not None else None
        self.height = int(height) if height is not None else None
        self._cv2 = cv2
        self._cap = cv2.VideoCapture(self.device_index)
        if not self._cap.isOpened():
            self._cap.release()
            self._cap = None
            raise RuntimeError(
                f"Could not open UVC device index {self.device_index} via "
                "OpenCV VideoCapture. Check the device is connected and not "
                "exclusively held by another process."
            )
        if self.width is not None:
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(self.width))
        if self.height is not None:
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self.height))

    def read_frame(self) -> OpticalLiveFrame:
        if self._cap is None:
            raise RuntimeError("UvcOpenCvSource is closed")
        ok, bgr = self._cap.read()
        if not ok or bgr is None:
            raise RuntimeError(
                f"Failed to read frame from UVC device index {self.device_index}"
            )
        intensity = extract_row(bgr, row=self.row)
        used_row = int(bgr.shape[0] // 2) if self.row is None else int(self.row)
        meta = {
            "synthetic": False,
            "source": "uvc_opencv",
            "device_index": self.device_index,
            "row": used_row,
            "frame_shape": list(bgr.shape),
            "wavelength_calibrated": False,
            "title": "Live UVC TeachSpec frame (intensity vs pixel)",
            "disclaimer": (
                "Live UVC capture via OpenCV — intensity vs pixel index only; "
                "not wavelength-calibrated by the camera alone. Apply "
                "teachspec.calibration (pixel→nm) separately. Not compound ID; "
                "not hardware-verified metrology. Subject to docs/family/teachspec/SAFETY.md."
            ),
        }
        return OpticalLiveFrame(intensity=intensity, meta=meta)

    def close(self) -> None:
        if self._cap is not None:
            try:
                self._cap.release()
            finally:
                self._cap = None

    def __enter__(self) -> UvcOpenCvSource:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def open_uvc_source(
    device_index: int = 0,
    row: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> OpticalFrameSource:
    """Open the live OpenCV UVC backend.

    Requires the ``[teachspec]`` extra (``opencv-python-headless``). Raises
    ``ImportError`` with install instructions if OpenCV is missing — never
    silently falls back to ``UvcIngestStub``.
    """
    return UvcOpenCvSource(
        device_index=device_index,
        row=row,
        width=width,
        height=height,
    )


__all__ = [
    "OpticalFrameSource",
    "UvcIngestStub",
    "UvcOpenCvSource",
    "extract_row",
    "open_uvc_source",
]
