from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


@pytest.fixture
def uvvis_csv() -> Path:
    return FIXTURES / "uvvis_synthetic.csv"


@pytest.fixture
def ir_csv() -> Path:
    return FIXTURES / "ir_synthetic.csv"
