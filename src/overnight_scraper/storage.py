from __future__ import annotations

import json
import sqlite3
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .models import Attempt, ColorMedia, Family, FamilyResult

TERMINAL_STATUSES = {
    "success",
    "partial",
    "sku_not_found",
    "needs_color_media_review",
    "failed",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS families (
            family_id TEXT PRIMARY KEY,
            representative_sku TEXT NOT NULL,
            declared_sku_count INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            source_sku TEXT,
            product_url TEXT,
            white_images TEXT NOT NULL DEFAULT '[]',
            white_videos TEXT NOT NULL DEFAULT '[]',
            yellow_images TEXT NOT NULL DEFAULT '[]',
            yellow_videos TEXT NOT NULL DEFAULT '[]',
            rose_images TEXT NOT NULL DEFAULT '[]',
            rose_videos TEXT NOT NULL DEFAULT '[]',
            attempts_json TEXT NOT NULL DEFAULT '[]',
            unrecognized_color_media TEXT NOT NULL DEFAULT '[]',
            error TEXT,
            started_at TEXT,
            finished_at TEXT,
            updated_at TEXT NOT NULL
        );
        """
    )
    connection.commit()


def seed_families(connection: sqlite3.Connection, families: Iterable[Family]) -> None:
    now = utc_now()
    connection.executemany(
        """
        INSERT OR IGNORE INTO families
            (family_id, representative_sku, declared_sku_count, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        [(family.family_id, family.representative_sku, family.declared_sku_count, now) for family in families],
    )
    connection.commit()


def pending_family_ids(connection: sqlite3.Connection) -> set[str]:
    placeholders = ",".join("?" for _ in TERMINAL_STATUSES)
    rows = connection.execute(
        f"SELECT family_id FROM families WHERE status NOT IN ({placeholders})",
        sorted(TERMINAL_STATUSES),
    )
    return {str(row["family_id"]) for row in rows}


def mark_running(connection: sqlite3.Connection, family_id: str) -> None:
    now = utc_now()
    connection.execute(
        """
        UPDATE families
        SET status = 'running', started_at = COALESCE(started_at, ?), updated_at = ?
        WHERE family_id = ?
        """,
        (now, now, family_id),
    )
    connection.commit()


def status_for_result(result: FamilyResult) -> str:
    color_review = any(
        media.evidence.get("color_swatch") is True
        and media.available is True
        and not media.evidence.get("color_specific")
        for media in (result.yellow_gold, result.rose_gold)
    )
    if result.unrecognized_color_media or color_review:
        return "needs_color_media_review"
    has_white = bool(result.white.images or result.white.videos)
    has_any_color = bool(
        result.yellow_gold.images
        or result.yellow_gold.videos
        or result.rose_gold.images
        or result.rose_gold.videos
    )
    if has_white and has_any_color:
        return "success"
    if has_white:
        return "partial"
    return "failed"


def save_result(connection: sqlite3.Connection, result: FamilyResult) -> str:
    now = utc_now()
    status = status_for_result(result)
    connection.execute(
        """
        UPDATE families
        SET status = ?, source_sku = ?, product_url = ?,
            white_images = ?, white_videos = ?,
            yellow_images = ?, yellow_videos = ?,
            rose_images = ?, rose_videos = ?,
            attempts_json = ?, unrecognized_color_media = ?,
            error = NULL, finished_at = ?, updated_at = ?
        WHERE family_id = ?
        """,
        (
            status,
            result.source_sku,
            result.product_url,
            json.dumps(result.white.images),
            json.dumps(result.white.videos),
            json.dumps(result.yellow_gold.images),
            json.dumps(result.yellow_gold.videos),
            json.dumps(result.rose_gold.images),
            json.dumps(result.rose_gold.videos),
            json.dumps([asdict(attempt) for attempt in result.attempts]),
            json.dumps(result.unrecognized_color_media),
            now,
            now,
            result.family_id,
        ),
    )
    connection.commit()
    return status


def save_not_found(connection: sqlite3.Connection, family_id: str, attempts: list[Attempt]) -> None:
    now = utc_now()
    connection.execute(
        """
        UPDATE families
        SET status = 'sku_not_found', attempts_json = ?, error = NULL,
            finished_at = ?, updated_at = ?
        WHERE family_id = ?
        """,
        (json.dumps([asdict(attempt) for attempt in attempts]), now, now, family_id),
    )
    connection.commit()


def save_failed(connection: sqlite3.Connection, family_id: str, attempts: list[Attempt], error: str) -> None:
    now = utc_now()
    connection.execute(
        """
        UPDATE families
        SET status = 'failed', attempts_json = ?, error = ?,
            finished_at = ?, updated_at = ?
        WHERE family_id = ?
        """,
        (json.dumps([asdict(attempt) for attempt in attempts]), error, now, now, family_id),
    )
    connection.commit()


def _media(images_json: str, videos_json: str, color_specific: bool) -> ColorMedia:
    return ColorMedia(
        json.loads(images_json),
        json.loads(videos_json),
        True,
        {"source": "sqlite", "color_specific": color_specific},
    )


def load_results(connection: sqlite3.Connection) -> list[FamilyResult]:
    rows = connection.execute("SELECT * FROM families WHERE product_url IS NOT NULL AND product_url != ''")
    results: list[FamilyResult] = []
    for row in rows:
        yellow_images = json.loads(row["yellow_images"])
        yellow_videos = json.loads(row["yellow_videos"])
        rose_images = json.loads(row["rose_images"])
        rose_videos = json.loads(row["rose_videos"])
        results.append(
            FamilyResult(
                family_id=row["family_id"],
                source_sku=row["source_sku"],
                product_url=row["product_url"],
                white=_media(row["white_images"], row["white_videos"], True),
                yellow_gold=ColorMedia(yellow_images, yellow_videos, True, {"source": "sqlite", "color_specific": bool(yellow_images or yellow_videos)}),
                rose_gold=ColorMedia(rose_images, rose_videos, True, {"source": "sqlite", "color_specific": bool(rose_images or rose_videos)}),
                attempts=[Attempt(**item) for item in json.loads(row["attempts_json"])],
                unrecognized_color_media=json.loads(row["unrecognized_color_media"]),
            )
        )
    return results


def progress(connection: sqlite3.Connection) -> dict[str, object]:
    rows = connection.execute("SELECT status, started_at, finished_at FROM families").fetchall()
    counts = Counter(str(row["status"]) for row in rows)
    total = len(rows)
    done = sum(counts[status] for status in TERMINAL_STATUSES)
    recent = connection.execute(
        """
        SELECT started_at, finished_at FROM families
        WHERE finished_at IS NOT NULL AND started_at IS NOT NULL
        ORDER BY finished_at DESC LIMIT 50
        """
    ).fetchall()
    durations = []
    for row in recent:
        started = datetime.fromisoformat(row["started_at"])
        finished = datetime.fromisoformat(row["finished_at"])
        duration = (finished - started).total_seconds()
        if duration > 0:
            durations.append(duration)
    seconds_per_family = sum(durations) / len(durations) if durations else None
    remaining = max(total - done, 0)
    return {
        "total": total,
        "done": done,
        "percent": round((done / total * 100), 2) if total else 0,
        "counts": dict(counts),
        "eta_seconds": int(seconds_per_family * remaining) if seconds_per_family else None,
    }
