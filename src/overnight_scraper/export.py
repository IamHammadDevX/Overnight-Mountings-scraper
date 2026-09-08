from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Optional
from openpyxl import load_workbook
from .models import ColorMedia, Family, FamilyResult

COLOR_COLUMNS = {
    "white": ("Images Link", "Videos Link"),
    "yellow_gold": ("Yellow Gold Images Link", "Yellow Gold Videos Link"),
    "rose_gold": ("Rose Gold Images Link", "Rose Gold Videos Link"),
}


def _link_map(urls: list[str]) -> Optional[str]:
    return str({str(index): url for index, url in enumerate(urls)}) if urls else None


def _write_color(row, headers: dict[str, int], media: ColorMedia, names: tuple[str, str]) -> None:
    # Preserve existing color cells unless scraper found confident media for that color.
    if media.available is not True or not media.evidence.get("color_specific"):
        return
    row[headers[names[0]] - 1].value = _link_map(media.images)
    row[headers[names[1]] - 1].value = _link_map(media.videos)


def _apply_results(sheet, families: Iterable[Family], results: Iterable[FamilyResult]) -> None:
    result_by_family = {result.family_id: result for result in results}
    result_by_sku = {
        sku: result_by_family[family.family_id]
        for family in families
        if family.family_id in result_by_family
        for sku in family.skus
    }
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


def export_master_copy(source_master: Path, output_path: Path, families: Iterable[Family], results: Iterable[FamilyResult]) -> None:
    """Create a new master workbook, changing only confirmed per-color media fields."""
    workbook = load_workbook(source_master, read_only=False, data_only=False)
    try:
        sheet = workbook["Overnight Products"]
        _apply_results(sheet, families, results)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        workbook.save(output_path)
    finally:
        workbook.close()


def export_master_csv(source_master: Path, output_path: Path, families: Iterable[Family], results: Iterable[FamilyResult]) -> None:
    """Create a CSV snapshot of the updated master sheet without modifying the source workbook."""
    workbook = load_workbook(source_master, read_only=False, data_only=False)
    try:
        sheet = workbook["Overnight Products"]
        _apply_results(sheet, families, results)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            for row in sheet.iter_rows(values_only=True):
                writer.writerow(["" if value is None else value for value in row])
    finally:
        workbook.close()
