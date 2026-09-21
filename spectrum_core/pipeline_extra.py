"""Register extra pipeline steps onto ``processing._OP_DISPATCH``.

Keeps derivative in the append-only pipeline without forking processing.py.
Not compound ID.
"""

from __future__ import annotations

from typing import Any, Mapping

from spectrum_core.processing import _OP_DISPATCH
from spectrum_core.quant import derivative_spectrum
from spectrum_core.spectrum import Spectrum


def op_derivative(
    spectrum: Spectrum,
    *,
    order: int = 1,
    window_length: int = 11,
    polyorder: int = 3,
) -> Spectrum:
    return derivative_spectrum(
        spectrum, order=order, window_length=window_length, polyorder=polyorder
    )


def _dispatch(spectrum: Spectrum, params: Mapping[str, Any]) -> Spectrum:
    kw: dict[str, Any] = {}
    if "order" in params:
        kw["order"] = int(params["order"])
    if "window_length" in params:
        kw["window_length"] = int(params["window_length"])
    if "polyorder" in params:
        kw["polyorder"] = int(params["polyorder"])
    return op_derivative(spectrum, **kw)


_OP_DISPATCH["derivative"] = _dispatch
