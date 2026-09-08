from __future__ import annotations

from datetime import date
from pathlib import Path

from .export import export_master_copy, export_master_csv
from .runner import run_full
from .storage import connect, init_db, load_results
from .workbooks import load_families


def current_run_id(today: date | None = None) -> str:
    year, week, _ = (today or date.today()).isocalendar()
    return f"{year}-W{week:02d}"


def run_weekly(
    requirements: Path,
    master: Path,
    runs_dir: Path = Path("data/runs"),
    downloads_dir: Path = Path("downloads"),
    run_id: str | None = None,
) -> Path:
    run_path = runs_dir / (run_id or current_run_id())
    db_path = run_path / "scraper.db"
    run_path.mkdir(parents=True, exist_ok=True)
    downloads_dir.mkdir(parents=True, exist_ok=True)

    run_full(requirements, db_path)

    families = load_families(requirements)
    connection = connect(db_path)
    try:
        init_db(connection)
        results = load_results(connection)
    finally:
        connection.close()

    export_master_copy(master, downloads_dir / "overnight_latest.xlsx", families, results)
    export_master_csv(master, downloads_dir / "overnight_latest.csv", families, results)
    return db_path
