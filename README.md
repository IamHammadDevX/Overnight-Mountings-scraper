# Overnight Mountings scraper

Family-based scraper for refreshing Overnight Mountings image/video URLs. Source Excel workbooks are inputs only and must never be overwritten.

## Scope

- Read 7,223 families from `Overnight_Unique_SKUs_For_Scraping.xlsx`.
- Resolve one representative SKU per family using public site search.
- Try another SKU in same family only after confirmed `not_found`.
- Capture White, Yellow Gold, and Rose Gold media separately from static product-page HTML.
- Do not copy White media into Yellow/Rose fields.
- Write production progress to SQLite first; export workbook copy separately on demand.

## Architecture

```text
src/overnight_scraper/
  workbooks.py  Read/validate requirement workbook; preserve SKU text
  models.py     Family, attempt, per-color media, result contracts
  http.py       Public SKU resolver; HTTP retries; page retrieval
  fallback.py   Required not-found-only family fallback policy
  media.py      Strict whitelist media extraction and color classification
  runner.py     Full resumable production runner
  storage.py    SQLite checkpointing; terminal-state resume; progress summaries
  status.py     SSH-friendly progress command with ETA
  sample.py     Bounded sample runner; one JSON evidence file per family
  review.py     CSV review report for sample JSON evidence
  export.py     New master-workbook copy from SQLite; never overwrites source input
  cli.py        inspect, sample, run, status, review, export commands

data/
  scraper.db    Resumable SQLite state for production run
  raw_results/  Per-family sample JSON evidence
  *.json        Validation and convention audits
  *.csv         Review reports

docs/
  color-media-decision.md  Deadline-safe color handling policy

tests/
  test_fallback.py  Not-found-only fallback tests
  test_media.py     Strict color-media parsing tests
  test_storage.py   SQLite resume test
```

## Color Media Rules

- Base image filenames: White.
- `.alt`, `.side.alt`, `.set.alt`: Yellow Gold images.
- `.alt1`, `.side.alt1`, `.set.alt1`: Rose Gold images.
- `.video.white`, base video filename: White video.
- `.video.yellow`: Yellow Gold video.
- `.video.rose`: Rose Gold video.
- Any other `.alt*` image suffix, including `.alt2`, `.alt3`, `.alt4`, `.alt5`, is stored in `unrecognized_color_media` and excluded from Yellow/Rose export columns.
- Missing color-specific assets preserve existing master-sheet values during export.

## Local Commands

```powershell
$env:PYTHONPATH = "src"
python -m overnight_scraper inspect "Overnight_Unique_SKUs_For_Scraping.xlsx"
python -m overnight_scraper sample "Overnight_Unique_SKUs_For_Scraping.xlsx" --limit 10 --output data/raw_results
python -m overnight_scraper run "Overnight_Unique_SKUs_For_Scraping.xlsx" --db data/scraper.db --limit 5
python -m overnight_scraper status --db data/scraper.db
python -m overnight_scraper export "Overnight_Unique_SKUs_For_Scraping.xlsx" "overnight_products_full_official_update.xlsx" --db data/scraper.db --output data/overnight_products_full_official_update_UPDATED.xlsx
python -m overnight_scraper review --input data/raw_results --output data/sample_review.csv
```

Production command has no `--limit`:

```bash
PYTHONPATH=src python -m overnight_scraper run "Overnight_Unique_SKUs_For_Scraping.xlsx" --db data/scraper.db
```

## Deployment Package

Transfer these to VPS:

- `src/`
- `tests/`
- `pyproject.toml`
- `requirements.txt`
- `README.md`
- `overnight-scraper.service`
- `Overnight_Unique_SKUs_For_Scraping.xlsx`
- `overnight_products_full_official_update.xlsx`
- `data/scraper.db`, only if local production progress already exists

Example transfer command, fill in user/IP:

```powershell
rsync -av --exclude ".git" --exclude ".venv" --exclude "__pycache__" D:/overnight-scraper/ USER@SERVER_IP:/opt/overnight-scraper/
```

If `rsync` is unavailable on Windows:

```powershell
scp -r D:\overnight-scraper USER@SERVER_IP:/opt/overnight-scraper
```

## Dallas VPS Setup

```bash
ssh USER@SERVER_IP
cat /etc/os-release
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip
cd /opt/overnight-scraper
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -e .
overnight-scraper inspect "Overnight_Unique_SKUs_For_Scraping.xlsx"
overnight-scraper run "Overnight_Unique_SKUs_For_Scraping.xlsx" --db data/scraper.db --limit 2
overnight-scraper status --db data/scraper.db
mkdir -p logs
sudo cp overnight-scraper.service /etc/systemd/system/overnight-scraper.service
sudo systemctl daemon-reload
sudo systemctl enable overnight-scraper
sudo systemctl start overnight-scraper
systemctl status overnight-scraper
```

Service uses `Restart=on-failure`, not `Restart=always`. `Restart=always` would restart even after a successful full completion and cause an endless finished-job restart loop.

## Monitoring

```bash
overnight-scraper status --db /opt/overnight-scraper/data/scraper.db
journalctl -u overnight-scraper -f
sudo systemctl stop overnight-scraper
sudo systemctl restart overnight-scraper
```

If SSH disconnects, systemd keeps running. If Python crashes, systemd restarts after 10 seconds. If VPS reboots, `WantedBy=multi-user.target` starts service again. On every start, SQLite terminal rows are skipped, so completed families are not re-scraped.

## Export

Export is separate from scraping and writes a new workbook copy only:

```bash
overnight-scraper export /opt/overnight-scraper/Overnight_Unique_SKUs_For_Scraping.xlsx /opt/overnight-scraper/overnight_products_full_official_update.xlsx --db /opt/overnight-scraper/data/scraper.db --output /opt/overnight-scraper/data/overnight_products_full_official_update_UPDATED.xlsx
```
