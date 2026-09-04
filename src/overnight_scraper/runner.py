from __future__ import annotations

from pathlib import Path
from typing import Optional

from .fallback import find_family_source
from .http import OvernightClient
from .media import parse_color_media, unrecognized_color_media
from .models import Attempt, FamilyResult, LookupOutcome
from .storage import (
    connect,
    init_db,
    mark_running,
    pending_family_ids,
    save_failed,
    save_not_found,
    save_result,
    seed_families,
)
from .workbooks import load_families


def capture_family(client: OvernightClient, family) -> tuple[Optional[FamilyResult], list[Attempt], Optional[str]]:
    attempts: list[Attempt] = []

    def lookup(sku: str) -> Attempt:
        page = client.resolve_sku(sku)
        attempt = Attempt(family.family_id, sku, page.url, page.outcome, page.detail)
        attempts.append(attempt)
        return attempt

    source = find_family_source(family, lookup)
    if source.outcome is LookupOutcome.NOT_FOUND:
        return None, attempts, None
    if source.outcome is not LookupOutcome.FOUND:
        return None, attempts, source.detail or source.outcome.value

    page = client.get_page(source.url or "")
    if page.outcome is not LookupOutcome.FOUND or page.html is None:
        return None, attempts, page.detail or page.outcome.value

    try:
        result = FamilyResult(
            family_id=family.family_id,
            source_sku=source.sku,
            product_url=page.url,
            white=parse_color_media(page.html, "White"),
            yellow_gold=parse_color_media(page.html, "Yellow"),
            rose_gold=parse_color_media(page.html, "Rose"),
            attempts=attempts,
            unrecognized_color_media=unrecognized_color_media(page.html),
        )
    except ValueError as error:
        return None, attempts, str(error)
    return result, attempts, None


def run_full(requirements: Path, db_path: Path, limit: Optional[int] = None) -> int:
    families = load_families(requirements)
    connection = connect(db_path)
    try:
        init_db(connection)
        seed_families(connection, families)
        pending = pending_family_ids(connection)
        client = OvernightClient()
        processed = 0
        for family in families:
            if family.family_id not in pending:
                continue
            if limit is not None and processed >= limit:
                break
            mark_running(connection, family.family_id)
            result, attempts, error = capture_family(client, family)
            if result is not None:
                status = save_result(connection, result)
            elif error is None:
                save_not_found(connection, family.family_id, attempts)
                status = "sku_not_found"
            else:
                save_failed(connection, family.family_id, attempts, error)
                status = "failed"
            processed += 1
            print(f"{family.family_id}: {status}", flush=True)
        return processed
    finally:
        connection.close()
