from __future__ import annotations

import json
from pathlib import Path
from overnight_scraper.browser import browser_capture_configuration_sample

if __name__ == "__main__":
    evidence = browser_capture_configuration_sample(
        Path("data/fullsite_browser_profile"),
        Path("data/fullsite_configuration_sample.xlsx"),
        Path("data/fullsite_configuration_sample.json"),
        "https://www.overnightmountings.com/product/85132-1",
    )
    print(json.dumps(evidence, indent=2))
