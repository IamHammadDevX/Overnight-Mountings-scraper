from __future__ import annotations

from pathlib import Path
from typing import Iterable
from openpyxl import load_workbook
from .models import ColorMedia, Family, FamilyResult

COLOR_COLUMNS = {
    "white": ("Images Link", "Videos Link"),
    "yellow_gold": ("Yellow Gold Images Link", "Yellow Gold Videos Link"),
    "rose_gold": ("Rose Gold Images Link", "Rose Gold Videos Link"),
}

def _link_map(urls: list[str]) -> str | None:
    return str({str(index): url for index, url in enumerate(urls)}) if urls else None

def _write_color(row, headers: dict[str, int], media: ColorMedia, names: tuple[str, str]) -> None:
    # Unknown means preserve old value. Confirmed unavailable means deliberately blank.
    if media.available is None:
        return
    row[headers[names[0]] - 1].value = _link_map(media.images) if media.available else None
    row[headers[names[1]] - 1].value = _link_map(media.videos) if media.available else None

def export_master_copy(source_master: Path, output_path: Path, families: Iterable[Family], results: Iterable[FamilyResult]) -> None:
    """Create a new master workbook, changing only confirmed per-color media fields."""
    result_by_family = {result.family_id: result for result in results}
    result_by_sku = {sku: result_by_family[family.family_id] for family in families if family.family_id in result_by_family for sku in family.skus}
    workbook = load_workbook(source_master, read_only=False, data_only=False)
    try:
        sheet = workbook["Overnight Products"]
        headers = {cell.value: cell.column for cell in sheet[1]}
        required = {"SKU", "Default_image_url", *(name for pair in COLOR_COLUMNS.values() for name in pair)}
        if missing := required - headers.keys():
            raise ValueError(f"Missing master columns: {sorted(missing)}")
        for row in sheet.iter_rows(min_row=2):
            result = result_by_sku.get(str(row[headers["SKU"] - 1].value))
            if result is None:
                continue
            _write_color(row, headers, result.white, COLOR_COLUMNS["white"])
            _write_color(row, headers, result.yellow_gold, COLOR_COLUMNS["yellow_gold"])
            _write_color(row, headers, result.rose_gold, COLOR_COLUMNS["rose_gold"])
            if result.white.available and result.white.images:
                row[headers["Default_image_url"] - 1].value = result.white.images[0]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        workbook.save(output_path)
    finally:
        workbook.close()
