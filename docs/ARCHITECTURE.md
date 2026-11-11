# Architecture

## Pipeline

```text
SEC company_tickers.json
        |
        v
companyfacts JSON per CIK
        |
        v
mapped us-gaap facts -> analytics/seeds/sec_facts.csv
        |
        v
dbt seed + dbt build -> data/warehouse/edgar.duckdb
        |
        +-> mart_balance_sheet
        +-> mart_income_statement
        +-> mart_cash_flow
        +-> mart_metric_history
        +-> mart_financial_screen
        |
        v
FastAPI read endpoints
```

## Grain

`sec_facts` has one row per XBRL fact after concept and unit filtering. `int_metric_facts` keeps one row per ticker and metric for each period. `mart_balance_sheet` has one row per ticker at each instant period end. `mart_income_statement` and `mart_cash_flow` have one row per ticker for each duration period. `mart_financial_screen` has one row per ticker for the latest fiscal year.

## Deduplication

SEC companyfacts contains overlapping facts across filings and frames. The ranking starts with concept priority. It then uses the latest filed date. Annual reports rank ahead of quarterly reports, which rank ahead of current reports. Accessions break ties.

## Concept mapping

`src/edgar_finance/concepts.py` is the source of truth. `ingest` writes `analytics/seeds/concept_map.csv` from it. The dbt intermediate model joins facts to that seed and filters by unit kind. USD covers statement amounts. USD per share covers EPS. Shares covers share counts.

## API

`serve.py` opens the DuckDB file read-only and exposes the marts as JSON. It does not mutate the warehouse.
