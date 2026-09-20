.PHONY: test install-ci

# Mirror CI: editable install with test/UI/baseline extras, then pytest.
install-ci:
	pip install -e ".[dev,ui,baselines]"

test: install-ci
	pytest -q
