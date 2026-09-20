# Release 0.2.0 checklist — chemspec-workbench

**Status:** prep Done in-repo; **PyPI / TestPyPI publish waits on maintainer credentials**
(user token — agents must **not** upload).

**Theme:** Measurement Integrity + TeachSpec UVC story.  
**Honesty:** no compound-ID claims; TeachSpec UVC = intensity vs pixel until calibrated;
public UV-Vis y is log₁₀(ε) → intensity, not absorbance.

## Pre-flight (already expected green on main)

- [ ] `git status` clean on the release commit / tag candidate
- [ ] `pip install -e ".[dev,ui,baselines,teachspec]"`
- [ ] `pytest -q` green (same as CI)
- [ ] Version is `0.2.0` in `pyproject.toml` and package `__version__` modules
- [ ] `CHANGELOG.md` `[0.2.0]` section reviewed
- [ ] README install / honesty blurb matches 0.2 story

## Build artifacts (local)

From a clean checkout with a fresh venv:

```bash
cd chemspec-workbench
python -m venv .venv && source .venv/bin/activate
pip install -U pip build twine
pip install -e ".[dev,ui,baselines]"
pytest -q
python -m build
```

Expect `dist/chemspec_workbench-0.2.0.tar.gz` and
`dist/chemspec_workbench-0.2.0-py3-none-any.whl` (setuptools normalizes the
distribution name with underscores in filenames; **PyPI project name** remains
`chemspec-workbench`).

## Twine check (no upload)

```bash
twine check dist/*
```

Both sdist and wheel should report **PASSED**.

## TestPyPI (maintainer — needs token)

Exact command when ready (replace token / use keyring as you prefer):

```bash
# One-time: create an API token at https://test.pypi.org/manage/account/#api-tokens
# Scope: entire account or project chemspec-workbench after first upload.

twine upload --repository testpypi dist/*
```

Or with an explicit token env (never commit the token):

```bash
TWINE_USERNAME=__token__ \
TWINE_PASSWORD=pypi-AgENdGVzdC5weXBpLm9yZw... \
twine upload --repository testpypi dist/*
```

Install from TestPyPI to smoke-test (pull deps from real PyPI):

```bash
pip install -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  chemspec-workbench==0.2.0
python -c "import spectrum_core, chemspec; print(spectrum_core.__version__, chemspec.__version__)"
```

## PyPI (maintainer — needs production token)

Only after TestPyPI smoke looks good:

```bash
twine upload dist/*
```

Then:

```bash
pip install chemspec-workbench==0.2.0
```

## Git tag (optional, maintainer)

```bash
git tag -a v0.2.0 -m "chemspec-workbench 0.2.0 — Measurement Integrity + TeachSpec UVC"
git push origin v0.2.0
```

## Out of scope for agents

- Actual `twine upload` (TestPyPI or PyPI)
- Storing or requesting PyPI tokens in CI without explicit maintainer setup
- NSF grant pitch rewrite / live classroom outreach emails

## Related

- Changelog: [`CHANGELOG.md`](../CHANGELOG.md)
- Classroom pilot ask: [`classroom_pilot_one_pager.md`](classroom_pilot_one_pager.md)
- TeachSpec safety: [`family/teachspec/SAFETY.md`](family/teachspec/SAFETY.md)
