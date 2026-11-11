from __future__ import annotations

import json
from pathlib import Path

from edgar_finance.concepts import CONCEPT_MAP
from edgar_finance.edgar import iter_company_facts
from edgar_finance.ingest import read_universe, write_concept_map

FIXTURE = Path(__file__).parent / "fixtures" / "companyfacts_sample.json"


def test_iter_company_facts_filters_to_concept_map() -> None:
    payload = json.loads(FIXTURE.read_text())
    rows = list(iter_company_facts(payload, "exm", concepts=set(CONCEPT_MAP)))

    assert len(rows) == 10
    assert {row["ticker"] for row in rows} == {"EXM"}
    assert "UnmappedExperimentalConcept" not in {row["concept"] for row in rows}
    assert all(row["taxonomy"] == "us-gaap" for row in rows)
    assert all(row["entity_name"] == "Example Financial Corp" for row in rows)


def test_iter_company_facts_keeps_instant_and_duration_shapes() -> None:
    payload = json.loads(FIXTURE.read_text())
    rows = list(iter_company_facts(payload, "EXM", concepts=set(CONCEPT_MAP)))
    by_concept = {row["concept"]: row for row in rows}

    assert by_concept["Assets"]["fact_start"] is None
    assert by_concept["Revenues"]["fact_start"] == "2024-01-01"
    assert by_concept["EarningsPerShareBasic"]["unit"] == "USD/shares"


def test_read_universe_normalizes_tickers(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    path.write_text("ticker,sector\njpm,Diversified Banks\nv,Payments\n")

    assert read_universe(path) == [
        {"ticker": "JPM", "sector": "Diversified Banks"},
        {"ticker": "V", "sector": "Payments"},
    ]


def test_write_concept_map_covers_python_map(tmp_path: Path) -> None:
    path = tmp_path / "concept_map.csv"
    write_concept_map(path)

    lines = path.read_text().splitlines()
    assert lines[0] == "concept,metric,statement,unit_kind,priority"
    assert len(lines) - 1 == len(CONCEPT_MAP)
