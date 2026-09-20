"""TeachSpec UVC ingest interface stub (no camera / no OpenCV)."""

from __future__ import annotations

import numpy as np
import pytest

from teachspec import (
    OpticalFrameSource,
    OpticalLiveFrame,
    UvcIngestStub,
    extract_row,
    generate_mock_frame,
)


def test_uvc_stub_read_frame_raises_not_implemented():
    stub = UvcIngestStub(device_index=0)
    with pytest.raises(NotImplementedError, match="Live UVC ingest is not Implemented"):
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
