from pathlib import Path

from chemspec.batch import run_folder


def test_batch_waterfall_fixture(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1] / "fixtures" / "waterfall"
    summary = run_folder(
        root,
        out_dir=tmp_path,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
        prominence=0.15,
        write_png=False,
        recursive=False,
    )
    assert summary["n_ok"] == 3
    assert summary["n_err"] == 0
    assert (tmp_path / "batch_summary.json").is_file()
    assert (tmp_path / "batch_index.csv").is_file()
    peaks = list(tmp_path.glob("*_peaks.csv"))
    assert len(peaks) == 3
