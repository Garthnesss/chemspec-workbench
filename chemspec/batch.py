"""Folder → peaks CSV + optional PNG. No compound ID.

    python -m chemspec.batch fixtures/waterfall --x-col wavelength_nm --y-col absorbance --x-unit nm --y-unit A
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from spectrum_core import (
    export_spectrum_png,
    find_peaks,
    ingest,
    list_spectrum_files,
    peaks_to_csv,
)


def run_folder(
    folder: Path,
    *,
    out_dir: Path,
    x_col: int | str,
    y_col: int | str,
    x_unit: str,
    y_unit: str,
    prominence: float,
    write_png: bool,
    recursive: bool,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = list_spectrum_files(folder, recursive=recursive)
    rows: list[dict] = []
    errors: list[dict] = []
    for path in files:
        try:
            spec = ingest(
                path,
                x_col=x_col,
                y_col=y_col,
                x_unit=x_unit,  # type: ignore[arg-type]
                y_unit=y_unit,  # type: ignore[arg-type]
            )
            peaks = find_peaks(spec, prominence=prominence)
            stem = path.stem
            (out_dir / f"{stem}_peaks.csv").write_text(peaks_to_csv(peaks), encoding="utf-8")
            if write_png:
                export_spectrum_png(spec, out_dir / f"{stem}.png", peaks=peaks or None)
            rows.append(
                {
                    "file": str(path),
                    "title": spec.title,
                    "n_points": len(spec),
                    "n_peaks": len(peaks),
                    "x_unit": spec.x_unit,
                    "y_unit": spec.y_unit,
                }
            )
        except Exception as exc:  # noqa: BLE001
            errors.append({"file": str(path), "error": str(exc)})
    summary = {
        "folder": str(folder),
        "n_files": len(files),
        "n_ok": len(rows),
        "n_err": len(errors),
        "prominence": prominence,
        "honesty": "batch_peaks_not_compound_id",
        "rows": rows,
        "errors": errors,
    }
    (out_dir / "batch_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    with (out_dir / "batch_index.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["file", "title", "n_points", "n_peaks", "x_unit", "y_unit"],
        )
        w.writeheader()
        w.writerows(rows)
    return summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="ChemSpec batch peaks (not compound ID)")
    p.add_argument("folder")
    p.add_argument("--out", default=None)
    p.add_argument("--x-col", default="0")
    p.add_argument("--y-col", default="1")
    p.add_argument("--x-unit", default="nm")
    p.add_argument("--y-unit", default="intensity")
    p.add_argument("--prominence", type=float, default=0.15)
    p.add_argument("--png", action="store_true")
    p.add_argument("--recursive", action="store_true")
    args = p.parse_args(argv)
    folder = Path(args.folder)
    out = Path(args.out) if args.out else folder / "_chemspec_batch"
    x_col: int | str = int(args.x_col) if str(args.x_col).isdigit() else args.x_col
    y_col: int | str = int(args.y_col) if str(args.y_col).isdigit() else args.y_col
    summary = run_folder(
        folder,
        out_dir=out,
        x_col=x_col,
        y_col=y_col,
        x_unit=args.x_unit,
        y_unit=args.y_unit,
        prominence=args.prominence,
        write_png=args.png,
        recursive=args.recursive,
    )
    print(f"ok={summary['n_ok']} err={summary['n_err']} → {out}")
    return 0 if summary["n_err"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
