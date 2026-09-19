"""Export peak tables to CSV (pure helper; UI may wrap for download)."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from spectrum_core.peaks import Peak

PEAK_CSV_FIELDS = ("index", "x", "y", "prominence")


def peaks_to_csv(
    peaks: list[Peak],
    path: str | Path | None = None,
    *,
    include_header: bool = True,
) -> str:
    """Serialize ``peaks`` to CSV text.

    Columns: ``index``, ``x``, ``y``, ``prominence`` (same order as
    ``PEAK_CSV_FIELDS``). If ``path`` is given, also write the text to that
    file (UTF-8, newline ``\\n``).

    Returns the CSV string (always).
    """
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(PEAK_CSV_FIELDS), lineterminator="\n")
    if include_header:
        writer.writeheader()
    for p in peaks:
        writer.writerow(
            {
                "index": p.index,
                "x": p.x,
                "y": p.y,
                "prominence": p.prominence,
            }
        )
    text = buf.getvalue()
    if path is not None:
        Path(path).write_text(text, encoding="utf-8")
    return text
