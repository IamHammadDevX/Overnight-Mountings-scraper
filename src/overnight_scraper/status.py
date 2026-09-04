from __future__ import annotations

from pathlib import Path
from typing import Optional

from .storage import connect, init_db, progress


def format_eta(seconds: Optional[int]) -> str:
    if seconds is None:
        return "unknown"
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def print_status(db_path: Path) -> None:
    connection = connect(db_path)
    try:
        init_db(connection)
        data = progress(connection)
    finally:
        connection.close()
    counts = data["counts"]
    print(f"Total families: {data['total']}")
    print(f"Complete: {data['done']} ({data['percent']}%)")
    for status in ("success", "partial", "sku_not_found", "needs_color_media_review", "failed", "running", "pending"):
        print(f"{status}: {counts.get(status, 0)}")
    print(f"ETA: {format_eta(data['eta_seconds'])}")
