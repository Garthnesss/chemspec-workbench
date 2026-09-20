"""TeachSpec UVC ingest: stub, extract_row, optional OpenCV (mocked; no camera)."""

from __future__ import annotations

import builtins
import sys
from typing import Any

import numpy as np
import pytest

from teachspec import (
    OpticalFrameSource,
    OpticalLiveFrame,
    UvcIngestStub,
    UvcOpenCvSource,
    extract_row,
    generate_mock_frame,
    open_uvc_source,
)
from teachspec import uvc_ingest as uvc_mod


def test_uvc_stub_read_frame_raises_not_implemented():
    stub = UvcIngestStub(device_index=0)
    with pytest.raises(NotImplementedError, match="UvcIngestStub does not capture"):
        stub.read_frame()


def test_uvc_stub_close_is_noop():
    stub = UvcIngestStub()
    assert stub.close() is None


def test_uvc_stub_satisfies_protocol_shape():
    stub = UvcIngestStub()
    assert isinstance(stub, OpticalFrameSource)


def test_mock_source_can_satisfy_protocol():
    """Document that mock path is the Phase-0 OpticalFrameSource stand-in."""

    class _MockAdapter:
        def read_frame(self) -> OpticalLiveFrame:
            frame, _truth = generate_mock_frame(n_pixels=64, seed=1)
            return frame

        def close(self) -> None:
            return None

    src: OpticalFrameSource = _MockAdapter()
    frame = src.read_frame()
    assert isinstance(frame, OpticalLiveFrame)
    assert frame.meta.get("synthetic") is True
    assert isinstance(src, OpticalFrameSource)


def test_extract_row_midline_and_rgb():
    img = np.arange(12, dtype=float).reshape(3, 4)
    row = extract_row(img)
    np.testing.assert_allclose(row, img[1, :])
    rgb = np.stack([img, img, img], axis=2)
    row_rgb = extract_row(rgb, row=0)
    np.testing.assert_allclose(row_rgb, img[0, :])


def test_extract_row_rejects_bad_shape():
    with pytest.raises(ValueError, match="2-D"):
        extract_row(np.arange(5))
    with pytest.raises(ValueError, match="out of range"):
        extract_row(np.zeros((2, 3)), row=5)


class _FakeCapture:
    """Minimal stand-in for cv2.VideoCapture (no hardware)."""

    CAP_PROP_FRAME_WIDTH = 3
    CAP_PROP_FRAME_HEIGHT = 4

    def __init__(self, device_index: int = 0, *, fail_open: bool = False) -> None:
        self.device_index = device_index
        self._opened = not fail_open
        self.released = False
        self.props: dict[int, float] = {}
        # BGR frame: bright mid-row
        self._frame = np.zeros((48, 64, 3), dtype=np.uint8)
        self._frame[24, :, :] = 200

    def isOpened(self) -> bool:
        return self._opened and not self.released

    def read(self) -> tuple[bool, np.ndarray | None]:
        if not self.isOpened():
            return False, None
        return True, self._frame.copy()

    def set(self, prop: int, value: float) -> bool:
        self.props[int(prop)] = float(value)
        return True

    def release(self) -> None:
        self.released = True
        self._opened = False


class _FakeCv2:
    CAP_PROP_FRAME_WIDTH = 3
    CAP_PROP_FRAME_HEIGHT = 4

    def __init__(self, *, fail_open: bool = False) -> None:
        self.fail_open = fail_open
        self.last_cap: _FakeCapture | None = None

    def VideoCapture(self, device_index: int) -> _FakeCapture:
        cap = _FakeCapture(device_index, fail_open=self.fail_open)
        self.last_cap = cap
        return cap


def test_uvc_opencv_source_with_fake_cv2(monkeypatch: pytest.MonkeyPatch):
    fake = _FakeCv2()
    monkeypatch.setattr(uvc_mod, "_import_cv2", lambda: fake)

    with UvcOpenCvSource(device_index=2, row=24, width=320, height=240) as src:
        assert isinstance(src, OpticalFrameSource)
        frame = src.read_frame()
        assert isinstance(frame, OpticalLiveFrame)
        assert frame.intensity.shape == (64,)
        assert frame.meta["source"] == "uvc_opencv"
        assert frame.meta["device_index"] == 2
        assert frame.meta["row"] == 24
        assert frame.meta["synthetic"] is False
        assert frame.meta["wavelength_calibrated"] is False
        assert "not wavelength-calibrated" in frame.meta["disclaimer"].lower()
        np.testing.assert_allclose(frame.intensity, np.full(64, 200.0))
        assert fake.last_cap is not None
        assert fake.last_cap.props[fake.CAP_PROP_FRAME_WIDTH] == 320.0
        assert fake.last_cap.props[fake.CAP_PROP_FRAME_HEIGHT] == 240.0

    assert fake.last_cap is not None
    assert fake.last_cap.released is True


def test_open_uvc_source_factory_uses_opencv(monkeypatch: pytest.MonkeyPatch):
    fake = _FakeCv2()
    monkeypatch.setattr(uvc_mod, "_import_cv2", lambda: fake)
    src = open_uvc_source(device_index=0)
    try:
        frame = src.read_frame()
        assert frame.meta["source"] == "uvc_opencv"
    finally:
        src.close()


def test_uvc_opencv_fails_clearly_when_device_not_opened(monkeypatch: pytest.MonkeyPatch):
    fake = _FakeCv2(fail_open=True)
    monkeypatch.setattr(uvc_mod, "_import_cv2", lambda: fake)
    with pytest.raises(RuntimeError, match="Could not open UVC device"):
        UvcOpenCvSource(device_index=9)


def test_uvc_opencv_import_error_when_cv2_missing(monkeypatch: pytest.MonkeyPatch):
    """Simulate missing OpenCV without uninstalling anything from the env."""

    real_import = builtins.__import__

    def _guarded_import(name: str, *args: Any, **kwargs: Any):
        if name == "cv2" or name.startswith("cv2."):
            raise ImportError("No module named 'cv2'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _guarded_import)
    monkeypatch.delitem(sys.modules, "cv2", raising=False)

    with pytest.raises(ImportError, match=r'pip install -e "\.\[teachspec\]"'):
        UvcOpenCvSource()

    with pytest.raises(ImportError, match="teachspec"):
        open_uvc_source()


def test_opencv_missing_message_mentions_mock_path():
    assert "teachspec" in uvc_mod._OPENCV_MISSING_MSG
    assert "mock" in uvc_mod._OPENCV_MISSING_MSG.lower()
