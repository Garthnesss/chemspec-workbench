"""Peak finder finds expected synthetic peaks within tolerance."""

from spectrum_core import find_peaks, ingest_csv


def _peak_xs(spec, prominence=0.15):
    return [p.x for p in find_peaks(spec, prominence=prominence)]


def test_uvvis_peaks_near_280_and_350(uvvis_csv):
    spec = ingest_csv(
        uvvis_csv,
        x_col="wavelength_nm",
        y_col="absorbance",
        x_unit="nm",
        y_unit="A",
    )
    xs = _peak_xs(spec, prominence=0.15)
    assert any(abs(x - 280) <= 8 for x in xs), f"no ~280 nm peak in {xs}"
    assert any(abs(x - 350) <= 10 for x in xs), f"no ~350 nm peak in {xs}"


def test_ir_peaks_near_1700_and_2900(ir_csv):
    spec = ingest_csv(
        ir_csv,
        x_col="wavenumber_cm-1",
        y_col="intensity",
        x_unit="cm-1",
        y_unit="intensity",
    )
    xs = _peak_xs(spec, prominence=0.15)
    assert any(abs(x - 1700) <= 30 for x in xs), f"no ~1700 cm-1 peak in {xs}"
    assert any(abs(x - 2900) <= 40 for x in xs), f"no ~2900 cm-1 peak in {xs}"
