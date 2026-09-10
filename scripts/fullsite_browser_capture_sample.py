from __future__ import annotations

import json
from pathlib import Path

from overnight_scraper.browser import browser_capture_sample

PROFILE_DIR = Path("data/fullsite_browser_profile")
OUTPUT_PATH = Path("data/fullsite_authenticated_sample.xlsx")
EVIDENCE_PATH = Path("data/fullsite_authenticated_capture.json")

if __name__ == "__main__":
    evidence = browser_capture_sample(PROFILE_DIR, OUTPUT_PATH, EVIDENCE_PATH, limit=5)
    print(json.dumps(evidence, indent=2))
