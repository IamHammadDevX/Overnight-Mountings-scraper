from __future__ import annotations
import argparse
from pathlib import Path
from .review import build_sample_review
from .sample import run_sample
from .workbooks import load_families

def main() -> None:
    parser = argparse.ArgumentParser(prog="overnight-scraper")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="validate requirements workbook")
    inspect.add_argument("requirements", type=Path)
    sample = commands.add_parser("sample", help="run bounded family sample")
    sample.add_argument("requirements", type=Path); sample.add_argument("--output", type=Path, default=Path("data/raw_results")); sample.add_argument("--limit", type=int, default=10); sample.add_argument("--start", type=int, default=0)
    review = commands.add_parser("review", help="create color-media review report")
    review.add_argument("--input", type=Path, default=Path("data/raw_results")); review.add_argument("--output", type=Path, default=Path("data/sample_review.csv"))
    args = parser.parse_args()
    if args.command == "inspect":
        families = load_families(args.requirements); print(f"Families: {len(families):,}\nUnique SKUs: {sum(f.declared_sku_count for f in families):,}")
    elif args.command == "sample":
        results = run_sample(args.requirements, args.output, args.limit, args.start); print(f"Captured {len(results)} of {args.limit} families")
    else:
        build_sample_review(args.input, args.output); print(f"Review report: {args.output}")

if __name__ == "__main__": main()
