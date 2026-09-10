"""Separate authenticated full-catalogue discovery and capture pipeline.

This module has no dependency on the 7,223-family workbook or its database.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from time import sleep
from typing import Iterable, Optional
from urllib.parse import urljoin, urlsplit, urlunsplit

from openpyxl import Workbook

from .http import BASE_URL, OvernightClient
from .media import parse_color_media, unrecognized_color_media
from .models import LookupOutcome

DEFAULT_CATALOG_SEEDS = (
    "/engagement_rings", "/wedding_bands", "/heads", "/jewelry_menu/",
    "/in_stock/", "/lattice_jewelry/", "/personalized_jewelry/", "/earrings",
    "/bracelets", "/fashion_rings", "/necklaces", "/pendants",
)
_PRODUCT_PATH = re.compile(r"^/product(?:/|$)", re.I)
_VARIANTS = re.compile(r'<script[^>]+id=["'']product-variants["''][^>]*>(.*?)</script>', re.I | re.S)
_PRICE = re.compile(r"\$\s*([0-9][0-9,]*(?:\.\d{2})?)")
_COMPLETE = re.compile(r"\bcomplete\b", re.I)
_SEMI_MOUNT = re.compile(r"\bsemi[- ]?mount\b", re.I)


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


@dataclass(frozen=True)
class CatalogPage:
    url: str
    category: str


@dataclass
class FullSiteProduct:
    product_url: str
    category: str
    sku: str = ""
    title: str = ""
    price: str = ""
    selected_finish: str = ""
    metal_type: str = ""
    metal_color: str = ""
    diamond_quality: str = ""
    finger_size: str = ""
    variant: str = ""
    white_images: list[str] = field(default_factory=list)
    white_videos: list[str] = field(default_factory=list)
    yellow_gold_images: list[str] = field(default_factory=list)
    yellow_gold_videos: list[str] = field(default_factory=list)
    rose_gold_images: list[str] = field(default_factory=list)
    rose_gold_videos: list[str] = field(default_factory=list)
    unrecognized_color_media: list[str] = field(default_factory=list)
    error: str = ""


class FullSiteClient(OvernightClient):
    """Session-aware client. Credentials are read only from environment vars."""

    def login_from_environment(self, username_env: str, password_env: str) -> None:
        username, password = os.environ.get(username_env), os.environ.get(password_env)
        if not username or not password:
            raise ValueError(f"Missing login credentials. Set {username_env} and {password_env} in the process environment.")
        login_url = urljoin(BASE_URL, "/account/login/")
        page = self._get(login_url)
        if not hasattr(page, "text") or not page.ok:
            raise RuntimeError("Could not load Overnight Mountings login page")
        token = re.search(r'name=["\']csrfmiddlewaretoken["\']\s+value=["\']([^"\']+)', page.text, re.I)
        if token is None:
            raise RuntimeError("Login form CSRF token was not found")
        response = self.session.post(
            login_url,
            data={"username": username, "password": password, "csrfmiddlewaretoken": token.group(1)},
            headers={"Referer": login_url}, timeout=self.timeout_seconds, allow_redirects=True,
        )
        # CAPTCHA must be completed through a client-approved browser session; do not bypass it.
        lower = response.text.lower()
        if "captcha" in lower or "/account/login" in response.url or 'id="loginform"' in lower:
            raise RuntimeError("Login requires browser/CAPTCHA completion. Do not bypass CAPTCHA.")
        if not response.ok:
            raise RuntimeError(f"Login failed: HTTP {response.status_code}")


def _canonical_url(raw_url: str) -> Optional[str]:
    absolute = urljoin(BASE_URL, raw_url)
    parts = urlsplit(absolute)
    if parts.scheme != "https" or parts.netloc.casefold() != urlsplit(BASE_URL).netloc.casefold():
        return None
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))


def _category_from_url(url: str) -> str:
    parts = [part for part in urlsplit(url).path.split("/") if part]
    return parts[0].replace("_", " ").title() if parts else "Home"


def extract_links(html: str, page_url: str) -> tuple[set[str], set[str]]:
    """Return product URLs and same-category pagination/filter URLs from one page."""
    parser = _LinkParser()
    parser.feed(html)
    products: set[str] = set()
    pages: set[str] = set()
    current_path = urlsplit(page_url).path.rstrip("/")
    for raw in parser.links:
        url = _canonical_url(urljoin(page_url, raw))
        if not url:
            continue
        path = urlsplit(url).path
        if _PRODUCT_PATH.match(path):
            products.add(url)
        elif path.rstrip("/") == current_path and urlsplit(url).query:
            pages.add(url)
    return products, pages


def _first(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(unescape(text))
    return match.group(1).strip() if match else ""


def _sku_from_product_html(product_url: str, html: str) -> str:
    """Get the exact current style number from the product-variants JSON payload."""
    match = _VARIANTS.search(html)
    if not match:
        return ""
    try:
        variants = json.loads(unescape(match.group(1)).strip())
    except json.JSONDecodeError:
        return ""
    slug = urlsplit(product_url).path.rstrip("/").rsplit("/", 1)[-1]
    if isinstance(variants, list):
        current = next((item for item in variants if isinstance(item, dict) and str(item.get("url", "")) == slug), None)
        if current is None:
            current = next((item for item in variants if isinstance(item, dict) and item.get("parent_product") is True), None)
        if isinstance(current, dict):
            return str(current.get("style_number", "")).strip()
    return ""

def _title(html: str) -> str:
    match = re.search(r"<h1[^>]*>\s*(.*?)\s*</h1>", html, re.I | re.S)
    return re.sub(r"<[^>]+>", "", unescape(match.group(1))).strip() if match else ""


def _finish(html: str) -> str:
    if _COMPLETE.search(html):
        return "Complete"
    if _SEMI_MOUNT.search(html):
        return "Semi-Mount"
    return ""


def product_from_html(product_url: str, category: str, html: str) -> FullSiteProduct:
    """Parse a product HTML document captured by requests or Playwright."""
    product = FullSiteProduct(
        product_url=product_url, category=category, sku=_sku_from_product_html(product_url, html),
        title=_title(html), price="", selected_finish=_finish(html),
    )
    try:
        white, yellow, rose = (parse_color_media(html, color) for color in ("White", "Yellow", "Rose"))
        product.white_images, product.white_videos = white.images, white.videos
        product.yellow_gold_images, product.yellow_gold_videos = yellow.images, yellow.videos
        product.rose_gold_images, product.rose_gold_videos = rose.images, rose.videos
        product.unrecognized_color_media = unrecognized_color_media(html)
    except ValueError as error:
        product.error = str(error)
    return product


def capture_product(client: FullSiteClient, product_url: str, category: str) -> FullSiteProduct:
    page = client.get_page(product_url)
    if page.outcome is not LookupOutcome.FOUND or page.html is None:
        return FullSiteProduct(product_url=product_url, category=category, error=page.detail or page.outcome.value)
    return product_from_html(page.url, category, page.html)


def discover_catalog(client: FullSiteClient, seeds: Iterable[str] = DEFAULT_CATALOG_SEEDS, limit_pages: Optional[int] = None, delay_seconds: float = 0.5) -> list[CatalogPage]:
    """Discover public product URLs from category pages, retaining category provenance."""
    queue = [url for seed in seeds if (url := _canonical_url(seed))]
    visited: set[str] = set()
    products: dict[str, CatalogPage] = {}
    while queue:
        page_url = queue.pop(0)
        if page_url in visited:
            continue
        if limit_pages is not None and len(visited) >= limit_pages:
            break
        visited.add(page_url)
        response = client.get_page(page_url)
        if response.outcome is not LookupOutcome.FOUND or response.html is None:
            continue
        category = _category_from_url(page_url)
        product_urls, more_pages = extract_links(response.html, page_url)
        for product_url in product_urls:
            products.setdefault(product_url, CatalogPage(product_url, category))
        queue.extend(sorted(url for url in more_pages if url not in visited and url not in queue))
        sleep(delay_seconds)
    return sorted(products.values(), key=lambda item: item.url)


FULLSITE_HEADERS = (
    "SKU", "Title", "Category", "Product URL", "Account Price", "Selected Finish", "Metal Type", "Metal Color", "Diamond Quality", "Finger Size", "Variant",
    "Images Link", "Videos Link", "Yellow Gold Images Link", "Yellow Gold Videos Link",
    "Rose Gold Images Link", "Rose Gold Videos Link", "Unrecognized Color Media", "Error",
)


def _links(urls: list[str]) -> str:
    return json.dumps({str(index): url for index, url in enumerate(urls)}) if urls else ""


def export_fullsite_workbook(products: Iterable[FullSiteProduct], output_path: Path) -> None:
    """Write a new standalone workbook; never reads or modifies prior workbooks."""
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("Overnight Full Site")
    sheet.append(FULLSITE_HEADERS)
    for product in products:
        sheet.append((
            product.sku, product.title, product.category, product.product_url, product.price, product.selected_finish, product.metal_type, product.metal_color, product.diamond_quality, product.finger_size, product.variant,
            _links(product.white_images), _links(product.white_videos), _links(product.yellow_gold_images), _links(product.yellow_gold_videos),
            _links(product.rose_gold_images), _links(product.rose_gold_videos),
            json.dumps(product.unrecognized_color_media) if product.unrecognized_color_media else "", product.error,
        ))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output_path)


def run_fullsite(output_path: Path, username_env: str, password_env: str, limit_pages: Optional[int] = None, limit_products: Optional[int] = None) -> tuple[int, int]:
    client = FullSiteClient()
    client.login_from_environment(username_env, password_env)
    catalogue = discover_catalog(client, limit_pages=limit_pages)
    if limit_products is not None:
        catalogue = catalogue[:limit_products]
    products = [capture_product(client, item.url, item.category) for item in catalogue]
    export_fullsite_workbook(products, output_path)
    return len(catalogue), len(products)









