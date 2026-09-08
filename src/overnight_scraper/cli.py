from __future__ import annotations
import argparse
from pathlib import Path
from .export import export_master_copy, export_master_csv
from .review import build_sample_review
from .runner import run_full
from .sample import run_sample
from .status import print_status
from .storage import connect, init_db, load_results
from .weekly import run_weekly
from .workbooks import load_families


def _results_from_db(db_path: Path):
    connection = connect(db_path)
    try:
        init_db(connection)
        return load_results(connection)
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="overnight-scraper")
    commands = parser.add_subparsers(dest="command", required=True)

    inspect = commands.add_parser("inspect", help="validate requirements workbook")
    inspect.add_argument("requirements", type=Path)

    sample = commands.add_parser("sample", help="run bounded family sample")
    sample.add_argument("requirements", type=Path)
    sample.add_argument("--output", type=Path, default=Path("data/raw_results"))
    sample.add_argument("--limit", type=int, default=10)
    sample.add_argument("--start", type=int, default=0)

    run = commands.add_parser("run", help="run resumable production scrape")
    run.add_argument("requirements", type=Path)
    run.add_argument("--db", type=Path, default=Path("data/scraper.db"))
    run.add_argument("--limit", type=int, default=None, help="optional smoke-test cap; omit for full production")

    status = commands.add_parser("status", help="show SQLite scrape progress")
    status.add_argument("--db", type=Path, default=Path("data/scraper.db"))

    review = commands.add_parser("review", help="create color-media review report")
    review.add_argument("--input", type=Path, default=Path("data/raw_results"))
    review.add_argument("--output", type=Path, default=Path("data/sample_review.csv"))

    export = commands.add_parser("export", help="write updated master workbook copy from SQLite results")
    export.add_argument("requirements", type=Path)
    export.add_argument("master", type=Path)
    export.add_argument("--db", type=Path, default=Path("data/scraper.db"))
    export.add_argument("--output", type=Path, default=Path("downloads/overnight_latest.xlsx"))

    export_csv = commands.add_parser("export-csv", help="write updated master CSV copy from SQLite results")
    export_csv.add_argument("requirements", type=Path)
    export_csv.add_argument("master", type=Path)
    export_csv.add_argument("--db", type=Path, default=Path("data/scraper.db"))
    export_csv.add_argument("--output", type=Path, default=Path("downloads/overnight_latest.csv"))

    weekly = commands.add_parser("weekly", help="run weekly refresh and publish latest CSV/XLSX files")
    weekly.add_argument("requirements", type=Path)
    weekly.add_argument("master", type=Path)
    weekly.add_argument("--runs-dir", type=Path, default=Path("data/runs"))
    weekly.add_argument("--downloads-dir", type=Path, default=Path("downloads"))
    weekly.add_argument("--run-id", default=None, help="optional fixed run id for testing/backfill")

    args = parser.parse_args()
    if args.command == "inspect":
        families = load_families(args.requirements)
        print(f"Families: {len(families):,}\nUnique SKUs: {sum(f.declared_sku_count for f in families):,}")
    elif args.command == "sample":
        results = run_sample(args.requirements, args.output, args.limit, args.start)
        print(f"Captured {len(results)} of {args.limit} families")
    elif args.command == "run":
        processed = run_full(args.requirements, args.db, args.limit)
        print(f"Processed {processed} families")
    elif args.command == "status":
        print_status(args.db)
    elif args.command == "export":
        families = load_families(args.requirements)
        export_master_copy(args.master, args.output, families, _results_from_db(args.db))
        print(f"Exported: {args.output}")
    elif args.command == "export-csv":
        families = load_families(args.requirements)
        export_master_csv(args.master, args.output, families, _results_from_db(args.db))
        print(f"Exported: {args.output}")
    elif args.command == "weekly":
        db_path = run_weekly(args.requirements, args.master, args.runs_dir, args.downloads_dir, args.run_id)
        print(f"Weekly run DB: {db_path}")
        print(f"Downloads: {args.downloads_dir / 'overnight_latest.csv'}, {args.downloads_dir / 'overnight_latest.xlsx'}")
    else:
        build_sample_review(args.input, args.output)
        print(f"Review report: {args.output}")


if __name__ == "__main__":
    main()
