# Overnight Mountings scraper

Family-based scraper for refreshing Overnight Mountings image/video URLs. Source Excel workbooks are inputs only and must never be overwritten.

## Scope

- Read 7,223 families from `Overnight_Unique_SKUs_For_Scraping.xlsx`.
- Resolve one representative SKU per family using public site search.
- Try another SKU in same family only after confirmed `not_found`.
- Capture White, Yellow Gold, and Rose Gold media separately from static product-page HTML.
- Do not copy White media into Yellow/Rose fields.
- Write scrape progress to SQLite first; export Excel/CSV copies separately.
- Publish fixed latest download files: `downloads/overnight_latest.csv` and `downloads/overnight_latest.xlsx`.

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
  weekly.py     Weekly per-run DB refresh plus latest CSV/XLSX publish
  sample.py     Bounded sample runner; one JSON evidence file per family
  review.py     CSV review report for sample JSON evidence
  export.py     New master workbook/CSV copies from SQLite; never overwrites source input
  cli.py        inspect, sample, run, status, review, export, export-csv, weekly commands

scripts/
  weekly_run.sh  Server-side weekly wrapper used by systemd timer

deploy/
  nginx-overnight.conf  Static download endpoint template

data/
  scraper.db     Optional one-off resumable SQLite state
  runs/YYYY-Www/ Weekly SQLite state, one DB per week
  raw_results/   Per-family sample JSON evidence

downloads/
  overnight_latest.csv   Client download target
  overnight_latest.xlsx  Client download target
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
python -m overnight_scraper export "Overnight_Unique_SKUs_For_Scraping.xlsx" "overnight_products_full_official update.xlsx" --db data/scraper.db --output downloads/overnight_latest.xlsx
python -m overnight_scraper export-csv "Overnight_Unique_SKUs_For_Scraping.xlsx" "overnight_products_full_official update.xlsx" --db data/scraper.db --output downloads/overnight_latest.csv
python -m overnight_scraper weekly "Overnight_Unique_SKUs_For_Scraping.xlsx" "overnight_products_full_official update.xlsx"
```

Production one-off command has no `--limit`:

```bash
PYTHONPATH=src python -m overnight_scraper run "Overnight_Unique_SKUs_For_Scraping.xlsx" --db data/scraper.db
```

## Deployment Package

Transfer these to VPS:

- `src/`
- `scripts/`
- `deploy/`
- `tests/`
- `pyproject.toml`
- `requirements.txt`
- `README.md`
- `overnight-scraper.service`
- `overnight-weekly.service`
- `overnight-weekly.timer`
- `Overnight_Unique_SKUs_For_Scraping.xlsx`
- `overnight_products_full_official update.xlsx`
- existing `data/runs/` or `data/scraper.db` only if resuming existing server/local progress

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
sudo apt install -y python3.11 python3.11-venv python3-pip nginx
cd /opt/overnight-scraper
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -e .
chmod +x scripts/weekly_run.sh
mkdir -p logs downloads data/runs
overnight-scraper inspect "Overnight_Unique_SKUs_For_Scraping.xlsx"
overnight-scraper run "Overnight_Unique_SKUs_For_Scraping.xlsx" --db data/scraper.db --limit 2
overnight-scraper status --db data/scraper.db
```

## Weekly Automation

Install timer and start weekly schedule:

```bash
sudo cp overnight-weekly.service /etc/systemd/system/overnight-weekly.service
sudo cp overnight-weekly.timer /etc/systemd/system/overnight-weekly.timer
sudo systemctl daemon-reload
sudo systemctl enable --now overnight-weekly.timer
systemctl list-timers overnight-weekly.timer
```

Run immediately once, without waiting for Sunday 02:00:

```bash
sudo systemctl start overnight-weekly.service
systemctl status overnight-weekly.service
```

Weekly service writes a fresh per-week DB under `data/runs/YYYY-Www/scraper.db`, preserving older weekly runs. It publishes fixed latest files:

```text
/opt/overnight-scraper/downloads/overnight_latest.csv
/opt/overnight-scraper/downloads/overnight_latest.xlsx
```

## Download Link

Install Nginx download endpoint:

```bash
sudo cp deploy/nginx-overnight.conf /etc/nginx/sites-available/overnight
sudo ln -s /etc/nginx/sites-available/overnight /etc/nginx/sites-enabled/overnight
sudo nginx -t
sudo systemctl reload nginx
```

Client links:

```text
http://SERVER_IP/overnight/overnight_latest.csv
http://SERVER_IP/overnight/overnight_latest.xlsx
```

With domain/TLS, replace `SERVER_IP` with domain.

## Monitoring

```bash
overnight-scraper status --db /opt/overnight-scraper/data/runs/$(date +%G-W%V)/scraper.db
journalctl -u overnight-weekly.service -f
sudo systemctl stop overnight-weekly.service
sudo systemctl restart overnight-weekly.service
```

If SSH disconnects, systemd keeps running. If Python crashes during weekly job, systemd restarts after 10 seconds. If VPS reboots, `Persistent=true` timer catches missed weekly runs. Within each weekly DB, completed terminal family rows are skipped on restart.

## Export Safety

Export writes new files only:

```bash
overnight-scraper export /opt/overnight-scraper/Overnight_Unique_SKUs_For_Scraping.xlsx "/opt/overnight-scraper/overnight_products_full_official update.xlsx" --db /opt/overnight-scraper/data/scraper.db --output /opt/overnight-scraper/downloads/overnight_latest.xlsx
overnight-scraper export-csv /opt/overnight-scraper/Overnight_Unique_SKUs_For_Scraping.xlsx "/opt/overnight-scraper/overnight_products_full_official update.xlsx" --db /opt/overnight-scraper/data/scraper.db --output /opt/overnight-scraper/downloads/overnight_latest.csv
```

Original input workbooks are never saved in place.

## Separate Full-Site Scrape (Paid Extension)

`fullsite` is isolated from the 7,223-family weekly pipeline. It creates a new
workbook only; it never reads, updates, or merges the existing client workbook.
Credentials are supplied at runtime through environment variables and are never
saved in the repository, command history, SQLite database, or Excel output.

```bash
export OVERNIGHT_USERNAME='client-provided-username'
export OVERNIGHT_PASSWORD='client-provided-password'
overnight-scraper fullsite --limit-pages 2 --limit-products 5
# Remove both limits only after the authenticated sample is approved.
```

The site currently presents CAPTCHA on its login page. If the account login
requires it, complete it only through a client-approved browser session; the
scraper does not bypass CAPTCHA. The full-site file is written separately to:

```text
downloads/fullsite/overnight_fullsite_latest.xlsx
```

