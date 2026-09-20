"""Shared scientific error types for spectrum_core.

Prefer these over bare ``ValueError`` in ingest / processing / measurement
paths so callers (UI, demos, tests) can catch a stable hierarchy. Both still
subclass ``ValueError`` for backward compatibility with existing handlers.
"""

from __future__ import annotations


class SpectrumError(ValueError):
    """Invalid spectrum data or scientifically invalid operation request."""


class ProcessingError(SpectrumError):
    """Pipeline / processing precondition failed (smooth, baseline, etc.)."""


__all__ = ["SpectrumError", "ProcessingError"]
