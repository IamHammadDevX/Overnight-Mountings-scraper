# Overnight Mountings scraper

Family-based scraper for refreshing Overnight Mountings image/video URLs. Source Excel workbooks are inputs only and must never be overwritten.

## Scope

- Read families from `Overnight_Unique_SKUs_For_Scraping.xlsx`.
- Resolve one representative SKU per family using public site search.
- Try another SKU in same family only after confirmed `not_found`.
- Capture structured White, Yellow Gold, and Rose Gold media separately.
- Do not copy White media into Yellow/Rose fields.
- Write results, evidence, reviews, and exported workbook copies under `data/`.

## Architecture

```text
src/overnight_scraper/
  workbooks.py  Read/validate requirement workbook; preserve SKU text
  models.py     Family, attempt, per-color media, result contracts
  http.py       Public SKU resolver; HTTP retries; page retrieval
  fallback.py   Required not-found-only family fallback policy
  media.py      Structured JSON media extraction and color URL classification
  sample.py     Bounded sample runner; one JSON evidence file per family
  review.py     CSV review report for missing color-specific media
  export.py     New master-workbook copy; never overwrites source input
  cli.py        inspect, sample, review commands

data/
  raw_results/  Per-family raw result/evidence JSON
  *.json        Small validation and convention audits
  *.csv         Review reports

docs/
  color-media-decision.md  Deadline-safe color handling policy

tests/
  test_fallback.py  Not-found-only fallback tests
  test_media.py     Structured color-media parsing tests
```

## Color media rules

- Base image filenames: White.
- `.alt` / `.alt2`: Yellow Gold.
- `.alt1` / `.alt4`: Rose Gold.
- `.video.white`, `.video.yellow`, `.video.rose`: matching color videos.
- Missing color-specific assets: preserve master-sheet value and log review status.

## Commands

```powershell
$env:PYTHONPATH = "src"
python -m overnight_scraper inspect "Overnight_Unique_SKUs_For_Scraping.xlsx"
python -m overnight_scraper sample "Overnight_Unique_SKUs_For_Scraping.xlsx" --limit 10 --output data/raw_results
python -m overnight_scraper review --input data/raw_results --output data/sample_review.csv
```

Run bounded samples and inspect evidence before scaling. Export must target a new workbook path.
