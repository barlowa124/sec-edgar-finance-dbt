from __future__ import annotations

import json
import os
import time
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
DEFAULT_USER_AGENT = os.environ.get(
    "SEC_USER_AGENT", "barlowa124 sec-edgar-finance-dbt barlowa124@gmail.com"
)


def fetch_json(url: str, user_agent: str = DEFAULT_USER_AGENT, timeout: float = 30.0) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def load_company_tickers(
    cache_path: str | Path | None = None,
    refresh: bool = False,
    user_agent: str = DEFAULT_USER_AGENT,
) -> dict[str, dict[str, Any]]:
    cache = Path(cache_path) if cache_path else None
    if cache and cache.exists() and not refresh:
        payload = json.loads(cache.read_text())
    else:
        payload = fetch_json(TICKERS_URL, user_agent=user_agent, timeout=60.0)
        if cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(payload, indent=2, sort_keys=True))

    tickers: dict[str, dict[str, Any]] = {}
    for row in payload.values():
        ticker = str(row.get("ticker", "")).upper()
        if ticker and ticker not in tickers:
            tickers[ticker] = {"cik": int(row["cik_str"]), "title": row.get("title", "")}
    return tickers


def companyfacts_url(cik: int) -> str:
    return f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"


def iter_company_facts(
    payload: dict[str, Any],
    ticker: str,
    concepts: set[str] | None = None,
) -> Iterator[dict[str, Any]]:
    entity_name = payload.get("entityName", "")
    cik = payload.get("cik")
    facts = payload.get("facts", {}).get("us-gaap", {})

    for concept, concept_obj in facts.items():
        if concepts is not None and concept not in concepts:
            continue
        units = concept_obj.get("units", {})
        label = concept_obj.get("label", concept)
        for unit, fact_list in units.items():
            for fact in fact_list:
                if not isinstance(fact, dict):
                    continue
                end = fact.get("end")
                val = fact.get("val")
                if end is None or val is None:
                    continue
                yield {
                    "cik": cik,
                    "ticker": ticker.upper(),
                    "entity_name": entity_name,
                    "taxonomy": "us-gaap",
                    "concept": concept,
                    "concept_label": label,
                    "unit": unit,
                    "fact_start": fact.get("start"),
                    "fact_end": end,
                    "val": val,
                    "accn": fact.get("accn"),
                    "fy": fact.get("fy"),
                    "fp": fact.get("fp"),
                    "form": fact.get("form"),
                    "filed": fact.get("filed"),
                    "frame": fact.get("frame"),
                }


def polite_sleep(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)
