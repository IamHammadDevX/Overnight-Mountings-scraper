from __future__ import annotations

import csv
import json
from pathlib import Path

def build_sample_review(raw_results: Path, report_path: Path) -> None:
    rows = []
    for result_path in sorted(raw_results.glob("FAM-*.json")):
        result = json.loads(result_path.read_text(encoding="utf-8"))
        status = "ready_for_white_export"
        notes = []
        for label, key in (("yellow_gold", "Yellow Gold"), ("rose_gold", "Rose Gold")):
            media = result.get(label, {})
            evidence = media.get("evidence", {})
            if media.get("available") is False:
                notes.append(f"{key} swatch unavailable")
            elif not evidence.get("color_specific", False):
                status = "needs_color_media_review"
                notes.append(f"{key} swatch has no color-specific structured media")
        rows.append({
            "family_id": result.get("family_id"),
            "source_sku": result.get("source_sku"),
            "product_url": result.get("product_url"),
            "white_images": len(result.get("white", {}).get("images", [])),
            "white_videos": len(result.get("white", {}).get("videos", [])),
            "status": status,
            "notes": "; ".join(notes),
        })
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["family_id"])
        writer.writeheader(); writer.writerows(rows)
