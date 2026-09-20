# Examples / tutorials

Short, runnable walkthroughs for ChemSpec / `spectrum_core`.

| Path | Time | Notes |
|------|------|--------|
| [`ethanol_ir_walkthrough.ipynb`](ethanol_ir_walkthrough.ipynb) | ~5–10 min | Public PNNL/NIST ethanol IR JCAMP → plot → baseline/smooth → peaks (FWHM/area) → optional CSV/session |
| [`ethanol_ir_walkthrough.py`](ethanol_ir_walkthrough.py) | headless twin | Same path; useful for smoke tests / CI without Jupyter |
| [`benzene_uvvis_walkthrough.ipynb`](benzene_uvvis_walkthrough.ipynb) | ~5–10 min | Public NIST benzene UV-Vis JCAMP → plot (log₁₀(ε) intensity, **not** A) → baseline/smooth → peaks → optional CSV/session |
| [`benzene_uvvis_walkthrough.py`](benzene_uvvis_walkthrough.py) | headless twin | Same path; pytest smoke / CI without Jupyter |
| [`acetone_uvvis_walkthrough.ipynb`](acetone_uvvis_walkthrough.ipynb) | ~5–10 min | Public NIST acetone UV-Vis JCAMP → plot (log₁₀(ε) intensity, **not** A) → baseline/smooth → peaks → optional CSV/session |
| [`acetone_uvvis_walkthrough.py`](acetone_uvvis_walkthrough.py) | headless twin | Same path; pytest smoke / CI without Jupyter |

## Setup

From the repo root (same extras as CI):

```bash
pip install -e ".[dev,ui,baselines]"
```

Notebook (matplotlib only — NiceGUI not required):

```bash
jupyter notebook examples/ethanol_ir_walkthrough.ipynb
```

Script:

```bash
python examples/ethanol_ir_walkthrough.py
python examples/ethanol_ir_walkthrough.py --save-dir /tmp/ethanol_ir_demo

python examples/benzene_uvvis_walkthrough.py
python examples/benzene_uvvis_walkthrough.py --save-dir /tmp/benzene_uvvis_demo

python examples/acetone_uvvis_walkthrough.py
python examples/acetone_uvvis_walkthrough.py --save-dir /tmp/acetone_uvvis_demo
```

## Honesty

These examples demonstrate an **analysis path** (ingest, process, peak metrics, export).
ChemSpec does **not** identify compounds. Public fixtures are labeled for provenance;
see [`fixtures/public/SOURCES.md`](../fixtures/public/SOURCES.md).

Notebook execute in CI is **not** required yet; pytest smokes the `.py` twin instead.
