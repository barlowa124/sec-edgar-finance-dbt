# Runs

## 2026-11-11 local build

Commands:

```bash
uv sync --extra analytics --extra dev
uv run pytest -q
uv run edgar-finance ingest
uv run dbt seed --full-refresh --project-dir analytics --profiles-dir analytics
uv run dbt build --project-dir analytics --profiles-dir analytics
```

Results:

- `pytest`: 9 passed.
- Ingest fetched all 15 tickers and wrote 68978 mapped facts with no errors. Snapshot SHA-256 `bc99465e1cc5e497584aefb2d008c717adad8bc915ae4bc8971e9563a9515296`.
- `dbt build`: all 52 checks passed.

Warehouse counts after the build:

| table | rows |
|---|---:|
| mart_balance_sheet | 1,029 |
| mart_income_statement | 1,619 |
| mart_cash_flow | 1,051 |
| mart_metric_history | 28,940 |
| mart_financial_screen | 15 |

The API smoke test used port 8017.

- `/health` returned `status: ok` and the mart counts above.
- `/screen?limit=3` returned the first three FY2025 screen rows with populated ratios.
- `/companies/JPM/income-statement?limit=2` returned the two latest JPM income rows.

Notes:

GS, MS, and WFC have no reported `Revenues` fact for FY2025. The income mart derives `revenue_effective` from interest and noninterest income for those filers. The screen reports `revenue_reported` next to `revenue` so the substitution stays visible.
