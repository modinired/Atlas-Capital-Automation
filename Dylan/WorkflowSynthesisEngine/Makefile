
.PHONY: format test unit integration lint

format:
	python -m pip install ruff black
	ruff check --fix cesar_src tests
	black cesar_src tests

lint:
	python -m pip install ruff mypy types-PyYAML types-requests
	ruff check cesar_src tests
	mypy cesar_src

unit:
	pytest -q -k "not integration"

integration:
	pytest -q -k integration

test: unit integration
