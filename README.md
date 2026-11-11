# sec-edgar-finance-dbt

SEC EDGAR XBRL data pipeline.

The code is Python. The warehouse is DuckDB. The API is FastAPI.

The repo fetches public company facts for a finance-heavy ticker universe. It normalizes the facts into canonical metrics. It builds dbt marts in DuckDB and serves them through a read API.

## What is inside

`src/edgar_finance/` holds the SEC client and FastAPI app. `analytics/` holds the dbt project. `analytics/seeds/` holds the universe and concept map. It also holds the generated facts snapshot. `tests/` covers the parser and API.

## Quickstart

```bash
uv sync --extra analytics --extra dev
uv run edgar-finance ingest
uv run dbt build --project-dir analytics --profiles-dir analytics
uv run edgar-finance serve --port 8000
```

The ingest command writes `analytics/seeds/sec_facts.csv` and `analytics/seeds/concept_map.csv`. It also writes `data/processed/ingest_manifest.json`. The dbt build writes `data/warehouse/edgar.duckdb`.

To refresh only a few tickers while iterating:

```bash
uv run edgar-finance ingest --tickers JPM,V,MA --delay 0.3
```

## API

After `make build`, run `uv run edgar-finance serve`. The service exposes `/health` and `/companies`. It also exposes `/screen`. Statement data is under `/companies/{ticker}/balance-sheet` and `/companies/{ticker}/income-statement`. Cash-flow data is under `/companies/{ticker}/cash-flow`. Metric history is under `/companies/{ticker}/metrics/{metric}` and `/metrics/{metric}`.

Example:

```bash
curl -s localhost:8000/companies/JPM/income-statement | jq '.[0]'
curl -s localhost:8000/screen | jq '.[] | {ticker, revenue, net_margin, debt_to_equity}'
```

## Data flow

SEC `company_tickers.json` resolves each ticker to a CIK. The ingest command fetches `companyfacts` JSON for that CIK and writes mapped `us-gaap` concepts to `sec_facts.csv`. Dbt seeds that file. Staging cleans dates and values. The intermediate model maps XBRL concepts to canonical metrics. Marts pivot the result into statement tables. `mart_metric_history` keeps the long metric view. `mart_financial_screen` keeps the latest fiscal-year screen. FastAPI reads those marts from DuckDB.

## Quality checks

Schema tests cover keys and nulls. They also check accepted values. Singular tests check for negative assets. They also check duplicate screen rows and duplicate income-statement periods. Pytest covers the SEC payload parser and API endpoints.

## Results

Latest local run is recorded in `data/processed/ingest_manifest.json` and `docs/RUNS.md`. The committed `sec_facts.csv` snapshot is the reproducible input for CI.

## Limits

XBRL tagging differs across filers and years. The concept map covers common tags and omits rare financial-statement variants.

The screen uses reported fiscal-year facts only. Restatements are handled by preferring the latest filed fact. The screen has no market-cap or price data.

Bank and non-bank revenue concepts differ. Treat `revenue` as a screening metric because GAAP revenue varies by filer.

Ratios such as `roe` and `debt_to_equity` are point-in-time screening ratios. They are inputs for review and should stay separate from valuation conclusions.
