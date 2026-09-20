#!/usr/bin/env bash
# Mirror GitHub Actions CI: clean editable install + full pytest.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python -m pip install -e ".[dev,ui,baselines]"
python -m pytest -q
