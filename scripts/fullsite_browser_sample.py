"""Visible Chromium sample for validating authenticated Overnight Mountings access.

Run locally, complete the normal browser login yourself, then press Enter in the
terminal. No password is read, logged, or written by this script.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = "https://www.overnightmountings.com"
PROFILE_DIR = Path("data/fullsite_browser_profile")
EVIDENCE_PATH = Path("data/fullsite_authenticated_sample.json")


def main() -> None:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR.resolve()),
            headless=False,
            viewport={"width": 1440, "height": 1000},
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(urljoin(BASE_URL, "/account/login/"), wait_until="domcontentloaded")
        input("Complete the normal Overnight login in Chromium, then press Enter here to validate the sample: ")
        page.goto(urljoin(BASE_URL, "/wedding_bands"), wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(5000)
        links = page.locator("a[href*='/product/']").evaluate_all(
            "elements => [...new Set(elements.map(item => item.href))]"
        )
        evidence = {
            "authenticated_url": page.url,
            "title": page.title(),
            "product_link_count": len(links),
            "product_links": links[:10],
            "profile_directory": str(PROFILE_DIR),
        }
        EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(json.dumps(evidence, indent=2))
        context.close()


if __name__ == "__main__":
    main()

