from __future__ import annotations

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .concepts import CONCEPT_MAP
from .edgar import (
    companyfacts_url,
    fetch_json,
    iter_company_facts,
    load_company_tickers,
    polite_sleep,
)

FIELDNAMES = [
    "cik",
    "ticker",
    "entity_name",
    "taxonomy",
    "concept",
    "concept_label",
    "unit",
    "fact_start",
    "fact_end",
    "val",
    "accn",
    "fy",
    "fp",
    "form",
    "filed",
    "frame",
    "retrieved_at",
]


def read_universe(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["ticker"] = row["ticker"].strip().upper()
        row["sector"] = row.get("sector", "").strip()
    return rows


def write_concept_map(path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["concept", "metric", "statement", "unit_kind", "priority"])
        writer.writeheader()
        for concept in sorted(CONCEPT_MAP):
            row = {"concept": concept, **CONCEPT_MAP[concept]}
            writer.writerow(row)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ingest(
    universe_path: str | Path,
    out_path: str | Path,
    concept_map_path: str | Path,
    manifest_path: str | Path,
    tickers: list[str] | None = None,
    limit: int | None = None,
    delay: float = 0.2,
    refresh_tickers: bool = False,
    user_agent: str | None = None,
    ticker_cache: str | Path = "data/raw/company_tickers.json",
) -> dict[str, Any]:
    out_path = Path(out_path)
    concept_map_path = Path(concept_map_path)
    manifest_path = Path(manifest_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    universe = read_universe(universe_path)
    if tickers:
        wanted = {ticker.strip().upper() for ticker in tickers}
        universe = [row for row in universe if row["ticker"] in wanted]
    if limit is not None:
        universe = universe[:limit]

    ticker_map = load_company_tickers(
        cache_path=ticker_cache,
        refresh=refresh_tickers,
        user_agent=user_agent or "barlowa124 sec-edgar-finance-dbt barlowa124@gmail.com",
    )
    write_concept_map(concept_map_path)

    retrieved_at = datetime.now(UTC).isoformat()
    rows_written = 0
    per_ticker: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    with out_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in universe:
            ticker = row["ticker"]
            info = ticker_map.get(ticker)
            if info is None:
                errors.append({"ticker": ticker, "error": "ticker not found in SEC company_tickers.json"})
                continue
            cik = info["cik"]
            url = companyfacts_url(cik)
            try:
                payload = fetch_json(url, user_agent=user_agent or "barlowa124 sec-edgar-finance-dbt barlowa124@gmail.com", timeout=60.0)
            except Exception as exc:  # noqa: BLE001 - record and continue so one issuer does not stop the run
                errors.append({"ticker": ticker, "error": str(exc)})
                polite_sleep(delay)
                continue

            before = rows_written
            for fact in iter_company_facts(payload, ticker, concepts=set(CONCEPT_MAP)):
                fact["retrieved_at"] = retrieved_at
                writer.writerow(fact)
                rows_written += 1
            per_ticker.append(
                {
                    "ticker": ticker,
                    "cik": cik,
                    "entity_name": payload.get("entityName", ""),
                    "sector": row.get("sector", ""),
                    "rows": rows_written - before,
                }
            )
            polite_sleep(delay)

    manifest = {
        "generated_at": retrieved_at,
        "universe_path": str(universe_path),
        "out_path": str(out_path),
        "concept_map_path": str(concept_map_path),
        "tickers_requested": len(universe),
        "tickers_fetched": len(per_ticker),
        "rows": rows_written,
        "errors": errors,
        "per_ticker": per_ticker,
        "sha256": sha256_file(out_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
