from __future__ import annotations

import duckdb
import pytest
from fastapi.testclient import TestClient

from edgar_finance.serve import create_app


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "edgar.duckdb"
    con = duckdb.connect(str(db_path))
    con.execute(
        """
        create table mart_financial_screen (
          ticker varchar,
          period_end date,
          revenue double,
          net_income double,
          net_margin double
        )
        """
    )
    con.execute(
        """
        create table mart_balance_sheet (
          ticker varchar,
          period_end date,
          assets double
        )
        """
    )
    con.execute(
        """
        create table mart_income_statement (
          ticker varchar,
          period_start date,
          period_end date,
          revenue double,
          net_income double
        )
        """
    )
    con.execute(
        """
        create table mart_cash_flow (
          ticker varchar,
          period_start date,
          period_end date,
          operating_cash_flow double,
          capex double
        )
        """
    )
    con.execute(
        """
        create table mart_metric_history (
          ticker varchar,
          metric varchar,
          statement varchar,
          unit_kind varchar,
          period_start date,
          period_end date,
          val double,
          form varchar,
          filed date,
          accn varchar,
          concept varchar,
          concept_priority integer
        )
        """
    )
    con.execute(
        "insert into mart_financial_screen values ('EXM', date '2024-12-31', 1000000, 120000, 0.12)"
    )
    con.execute("insert into mart_balance_sheet values ('EXM', date '2024-12-31', 5000000)")
    con.execute(
        "insert into mart_income_statement values ('EXM', date '2024-01-01', date '2024-12-31', 1000000, 120000)"
    )
    con.execute(
        "insert into mart_cash_flow values ('EXM', date '2024-01-01', date '2024-12-31', 220000, 40000)"
    )
    con.execute(
        """
        insert into mart_metric_history values
        ('EXM', 'revenue', 'income', 'usd', date '2024-01-01', date '2024-12-31', 1000000, '10-K', date '2025-02-15', 'accn', 'Revenues', 3)
        """
    )
    con.close()

    return TestClient(create_app(db_path=db_path))


def test_health_reports_table_counts(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["counts"]["mart_financial_screen"] == 1


def test_companies_endpoint_returns_screen(client: TestClient) -> None:
    response = client.get("/companies")
    assert response.status_code == 200
    assert response.json()[0]["ticker"] == "EXM"


def test_income_statement_endpoint_is_case_insensitive(client: TestClient) -> None:
    response = client.get("/companies/exm/income-statement")
    assert response.status_code == 200
    rows = response.json()
    assert rows[0]["revenue"] == 1000000
    assert rows[0]["period_end"] == "2024-12-31"


def test_metric_history_endpoint(client: TestClient) -> None:
    response = client.get("/companies/EXM/metrics/revenue")
    assert response.status_code == 200
    assert response.json()[0]["metric"] == "revenue"


def test_missing_database_returns_503(tmp_path) -> None:
    client = TestClient(create_app(db_path=tmp_path / "missing.duckdb"))
    response = client.get("/health")
    assert response.status_code == 503
