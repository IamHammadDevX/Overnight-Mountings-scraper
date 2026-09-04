from __future__ import annotations
from dataclasses import asdict
import json
from pathlib import Path
from .fallback import find_family_source
from .http import OvernightClient
from .models import Attempt, ColorMedia, FamilyResult, LookupOutcome
from .workbooks import load_families

def run_sample(requirements: Path, output: Path, limit: int = 10, start: int = 0) -> list[FamilyResult]:
    client, results = OvernightClient(), []
    output.mkdir(parents=True, exist_ok=True)
    for family in load_families(requirements)[start:start + limit]:
        attempts: list[Attempt] = []
        def lookup(sku: str) -> Attempt:
            page = client.resolve_sku(sku)
            attempt = Attempt(family.family_id, sku, page.url, page.outcome, page.detail)
            attempts.append(attempt)
            return attempt
        source = find_family_source(family, lookup)
        if source.outcome is not LookupOutcome.FOUND:
            (output / f"{family.family_id}.json").write_text(json.dumps({"family_id": family.family_id, "attempts": [asdict(x) for x in attempts]}, indent=2), encoding="utf-8")
            continue
        colors: dict[str, ColorMedia] = {}
        for label, parameter in (("white", "White"), ("yellow_gold", "Yellow"), ("rose_gold", "Rose")):
            page, media = client.capture_color(source.url or "", parameter)
            colors[label] = media if media is not None else ColorMedia(available=None, evidence={"error": page.detail, "url": page.url})
        result = FamilyResult(family.family_id, source.sku, source.url or "", colors["white"], colors["yellow_gold"], colors["rose_gold"], attempts)
        results.append(result)
        (output / f"{family.family_id}.json").write_text(json.dumps(result.as_dict(), indent=2), encoding="utf-8")
    return results

