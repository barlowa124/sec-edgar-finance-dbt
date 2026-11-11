from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb
from fastapi import FastAPI, HTTPException, Query

from . import __version__

DEFAULT_DB_PATH = os.environ.get("EDGAR_DUCKDB_PATH", "data/warehouse/edgar.duckdb")


def jsonable(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def rows_to_dicts(cursor: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    columns = [description[0] for description in cursor.description]
    return [{column: jsonable(value) for column, value in zip(columns, row)} for row in cursor.fetchall()]


def create_app(db_path: str | Path | None = None) -> FastAPI:
    db_path = Path(db_path or os.environ.get("EDGAR_DUCKDB_PATH", DEFAULT_DB_PATH))
    app = FastAPI(title="sec-edgar-finance", version=__version__)

    def connect() -> duckdb.DuckDBPyConnection:
        if not db_path.exists():
            raise HTTPException(
                status_code=503,
                detail=f"DuckDB file not found at {db_path}. Run `make ingest` and `make build` first.",
            )
        try:
            return duckdb.connect(str(db_path), read_only=True)
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Could not open {db_path}: {exc}") from exc

    def query(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        con = connect()
        try:
            return rows_to_dicts(con.execute(sql, params))
        finally:
            con.close()

    @app.get("/health")
    def health() -> dict[str, Any]:
        con = connect()
        try:
            counts = {}
            for table in ["mart_balance_sheet", "mart_income_statement", "mart_cash_flow", "mart_financial_screen"]:
                counts[table] = con.execute(f"select count(*) from {table}").fetchone()[0]
            return {"status": "ok", "db": str(db_path), "counts": counts}
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Database is not built: {exc}") from exc
        finally:
            con.close()

    @app.get("/companies")
    def companies(limit: int = Query(default=100, ge=1, le=500)) -> list[dict[str, Any]]:
        return query(
            "select * from mart_financial_screen order by ticker limit ?",
            (limit,),
        )

    @app.get("/screen")
    def screen(limit: int = Query(default=100, ge=1, le=500)) -> list[dict[str, Any]]:
        return query(
            "select * from mart_financial_screen order by ticker limit ?",
            (limit,),
        )

    @app.get("/companies/{ticker}/balance-sheet")
    def balance_sheet(
        ticker: str,
        limit: int = Query(default=40, ge=1, le=500),
    ) -> list[dict[str, Any]]:
        return query(
            "select * from mart_balance_sheet where upper(ticker) = upper(?) order by period_end desc limit ?",
            (ticker, limit),
        )

    @app.get("/companies/{ticker}/income-statement")
    def income_statement(
        ticker: str,
        limit: int = Query(default=40, ge=1, le=500),
    ) -> list[dict[str, Any]]:
        return query(
            "select * from mart_income_statement where upper(ticker) = upper(?) order by period_end desc limit ?",
            (ticker, limit),
        )

    @app.get("/companies/{ticker}/cash-flow")
    def cash_flow(
        ticker: str,
        limit: int = Query(default=40, ge=1, le=500),
    ) -> list[dict[str, Any]]:
        return query(
            "select * from mart_cash_flow where upper(ticker) = upper(?) order by period_end desc limit ?",
            (ticker, limit),
        )

    @app.get("/companies/{ticker}/metrics/{metric}")
    def metric_history(
        ticker: str,
        metric: str,
        limit: int = Query(default=80, ge=1, le=1000),
    ) -> list[dict[str, Any]]:
        return query(
            """
            select *
            from mart_metric_history
            where upper(ticker) = upper(?) and metric = ?
            order by period_end desc
            limit ?
            """,
            (ticker, metric, limit),
        )

    @app.get("/metrics/{metric}")
    def metric(metric: str, limit: int = Query(default=500, ge=1, le=5000)) -> list[dict[str, Any]]:
        return query(
            "select * from mart_metric_history where metric = ? order by ticker, period_end desc limit ?",
            (metric, limit),
        )

    return app


app = create_app()
