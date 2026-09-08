#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/overnight-scraper}"
REQUIREMENTS_FILE="${REQUIREMENTS_FILE:-$PROJECT_DIR/Overnight_Unique_SKUs_For_Scraping.xlsx}"
MASTER_FILE="${MASTER_FILE:-$PROJECT_DIR/overnight_products_full_official update.xlsx}"
RUNS_DIR="${RUNS_DIR:-$PROJECT_DIR/data/runs}"
DOWNLOADS_DIR="${DOWNLOADS_DIR:-$PROJECT_DIR/downloads}"

cd "$PROJECT_DIR"
mkdir -p "$RUNS_DIR" "$DOWNLOADS_DIR" "$PROJECT_DIR/logs"
"$PROJECT_DIR/.venv/bin/overnight-scraper" weekly "$REQUIREMENTS_FILE" "$MASTER_FILE" --runs-dir "$RUNS_DIR" --downloads-dir "$DOWNLOADS_DIR"
