# dbt analytics

This directory contains the dbt project for the SEC EDGAR finance pipeline.

## Commands

From the repository root:

```bash
uv run edgar-finance ingest
uv run dbt build --project-dir analytics --profiles-dir analytics
```

The profile writes to `data/warehouse/edgar.duckdb` relative to the repository root.

## Layers

Staging casts the generated `sec_facts` seed into typed columns. The intermediate model maps XBRL concepts to canonical metrics and deduplicates facts. Marts pivot metrics into statement tables. `mart_metric_history` keeps the long metric view. `mart_financial_screen` keeps the latest fiscal-year screen.

## Tests

Schema tests live beside the models and seeds. Singular tests live in `tests/`. They check for negative assets. They also check duplicate screen rows and duplicate income-statement periods.
