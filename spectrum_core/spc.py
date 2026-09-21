"""Thermo Galactic / GRAMS ``.spc`` reader. First subfile only.

Supported: new little-endian header (``fversn = 0x4B``), even-X or global
TXVALS X, IEEE float or scaled int32 Y. Not XYXY per-subfile, not old 0x4D,
not big-endian 0x4C. Not compound ID.
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Any

import numpy as np

from spectrum_core.spectrum import Spectrum, XUnit, YUnit

_TXVALS = 0x80
_TXYXYS = 0x40

_X_MAP: dict[int, XUnit] = {
    1: "cm-1",
    3: "nm",
    6: "Hz",
    7: "Hz",
    8: "Hz",
    10: "ppm",
}
_Y_MAP: dict[int, YUnit] = {
    2: "A",
    11: "percent_T",
}


def is_spc_path(path: str | Path) -> bool:
    return Path(path).suffix.lower() == ".spc"


def _x_unit(code: int) -> XUnit:
    return _X_MAP.get(int(code), "nm")


def _y_unit(code: int) -> YUnit:
    return _Y_MAP.get(int(code), "intensity")


def ingest_spc(
    path: str | Path,
    *,
    title: str | None = None,
    meta: dict[str, Any] | None = None,
) -> Spectrum:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(p)
    blob = p.read_bytes()
    if len(blob) < 512 + 32:
        raise ValueError(f"SPC too short for header+subfile: {p}")
    ftflgs = blob[0]
    fversn = blob[1]
    fexp = blob[3]
    if fversn != 0x4B:
        raise ValueError(
            f"SPC version 0x{fversn:02X} not supported "
            "(need new little-endian 0x4B)"
        )
    if ftflgs & _TXYXYS:
        raise ValueError(
            "SPC TXYXYS (per-subfile X) not supported yet; export CSV/JCAMP"
        )
    fnpts = struct.unpack_from("<i", blob, 4)[0]
    ffirst, flast = struct.unpack_from("<dd", blob, 8)
    fnsub = struct.unpack_from("<i", blob, 24)[0]
    fxtype, fytype = blob[28], blob[29]
    if fnpts < 2:
        raise ValueError(f"SPC fnpts must be ≥2 (got {fnpts})")
    off = 512
    if ftflgs & _TXVALS:
        need = off + fnpts * 4
        if len(blob) < need:
            raise ValueError(f"SPC truncated in global X array: {p}")
        x = np.frombuffer(blob, dtype="<f4", count=fnpts, offset=off).astype(float)
        off = need
    else:
        x = np.linspace(float(ffirst), float(flast), int(fnpts))
    if off + 32 > len(blob):
        raise ValueError(f"SPC truncated before subheader: {p}")
    subexp = blob[off + 1]
    subnpts_field = struct.unpack_from("<i", blob, off + 16)[0]
    n = int(subnpts_field) if subnpts_field > 0 else int(fnpts)
    if n < 2:
        raise ValueError(f"SPC subfile npts must be ≥2 (got {n})")
    off += 32
    exp = subexp if subexp != 0 else fexp
    if exp == 0x80:
        need = off + n * 4
        if len(blob) < need:
            raise ValueError(f"SPC truncated in float Y: {p}")
        y = np.frombuffer(blob, dtype="<f4", count=n, offset=off).astype(float)
    else:
        need = off + n * 4
        if len(blob) < need:
            raise ValueError(f"SPC truncated in scaled Y: {p}")
        raw = np.frombuffer(blob, dtype="<i4", count=n, offset=off).astype(float)
        y = raw * (2.0 ** (int(exp) - 32))
    if x.size != y.size:
        x = x[: y.size]
    extra = {
        "source_format": "spc",
        "spc_fversn": f"0x{fversn:02X}",
        "spc_fxtype": int(fxtype),
        "spc_fytype": int(fytype),
        "spc_fnsub": int(fnsub),
        "spc_subfile": 0,
        "honesty": "first_subfile_only_not_compound_id",
    }
    if fnsub > 1:
        extra["spc_note"] = f"file has {fnsub} subfiles; loaded index 0 only"
    return Spectrum(
        x=np.asarray(x, dtype=float),
        y=np.asarray(y, dtype=float),
        x_unit=_x_unit(fxtype),
        y_unit=_y_unit(fytype),
        title=title or p.stem,
        meta={**(meta or {}), **extra},
    )


def write_spc_even_x(
    path: str | Path,
    x: np.ndarray,
    y: np.ndarray,
    *,
    x_type: int = 3,
    y_type: int = 2,
) -> None:
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    if x.size != y.size or x.size < 2:
        raise ValueError("write_spc_even_x: x and y must be same length ≥ 2")
    n = int(x.size)
    hdr = bytearray(512)
    hdr[0] = 0
    hdr[1] = 0x4B
    hdr[3] = 0x80
    struct.pack_into("<i", hdr, 4, n)
    struct.pack_into("<d", hdr, 8, float(x[0]))
    struct.pack_into("<d", hdr, 16, float(x[-1]))
    struct.pack_into("<i", hdr, 24, 1)
    hdr[28] = int(x_type) & 0xFF
    hdr[29] = int(y_type) & 0xFF
    sub = bytearray(32)
    sub[1] = 0x80
    struct.pack_into("<i", sub, 16, n)
    yb = np.asarray(y, dtype="<f4").tobytes()
    Path(path).write_bytes(bytes(hdr) + bytes(sub) + yb)
