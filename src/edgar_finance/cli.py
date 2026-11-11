from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from .ingest import ingest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="edgar-finance", description="SEC EDGAR finance analytics pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Fetch SEC companyfacts and write dbt seeds")
    ingest_parser.add_argument("--universe", default="analytics/seeds/company_universe.csv")
    ingest_parser.add_argument("--out", default="analytics/seeds/sec_facts.csv")
    ingest_parser.add_argument("--concept-map-out", default="analytics/seeds/concept_map.csv")
    ingest_parser.add_argument("--manifest", default="data/processed/ingest_manifest.json")
    ingest_parser.add_argument("--tickers", help="Comma-separated ticker subset")
    ingest_parser.add_argument("--limit", type=int, default=None)
    ingest_parser.add_argument("--delay", type=float, default=0.2)
    ingest_parser.add_argument("--refresh-tickers", action="store_true")
    ingest_parser.add_argument("--user-agent", default=None)

    build_parser = subparsers.add_parser("build", help="Run dbt build for the analytics project")
    build_parser.add_argument("--project-dir", default="analytics")
    build_parser.add_argument("--profiles-dir", default="analytics")
    build_parser.add_argument("--full-refresh", action="store_true")

    serve_parser = subparsers.add_parser("serve", help="Run the FastAPI read API")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.add_argument("--reload", action="store_true")
    serve_parser.add_argument("--db", default=None, help="Override EDGAR_DUCKDB_PATH")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "ingest":
        tickers = [item.strip() for item in args.tickers.split(",")] if args.tickers else None
        manifest = ingest(
            universe_path=args.universe,
            out_path=args.out,
            concept_map_path=args.concept_map_out,
            manifest_path=args.manifest,
            tickers=tickers,
            limit=args.limit,
            delay=args.delay,
            refresh_tickers=args.refresh_tickers,
            user_agent=args.user_agent,
        )
        print(f"wrote {manifest['rows']} rows for {manifest['tickers_fetched']} tickers to {args.out}")
        if manifest["errors"]:
            print(f"errors: {len(manifest['errors'])}")
        return 0

    if args.command == "build":
        dbt = shutil.which("dbt") or "dbt"
        command = [dbt, "build", "--project-dir", args.project_dir, "--profiles-dir", args.profiles_dir]
        if args.full_refresh:
            command.append("--full-refresh")
        return subprocess.run(command, check=False).returncode

    if args.command == "serve":
        import os

        if args.db:
            os.environ["EDGAR_DUCKDB_PATH"] = str(Path(args.db).resolve())
        import uvicorn

        uvicorn.run("edgar_finance.serve:app", host=args.host, port=args.port, reload=args.reload)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
