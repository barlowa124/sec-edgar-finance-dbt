PYTHON ?= uv run python
DBT ?= uv run dbt

.PHONY: ingest build test serve lint

ingest:
	uv run edgar-finance ingest

build:
	$(DBT) build --project-dir analytics --profiles-dir analytics

test:
	uv run pytest -q

serve:
	uv run edgar-finance serve --port 8000

lint:
	uv run ruff check src tests
