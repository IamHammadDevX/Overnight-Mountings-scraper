"""Playwright helpers for the authenticated, configuration-level full-site scraper."""
from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit

from playwright.sync_api import sync_playwright

from .fullsite import BASE_URL, FullSiteProduct, export_fullsite_workbook, product_from_html


def _goto(page, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    page.wait_for_timeout(1_500)


def _variant_details(html: str) -> dict[str, tuple[str, str]]:
    """Map each displayed variant label to its exact SKU and canonical product URL."""
    match = re.search(r'<script[^>]+id=["\']product-variants["\'][^>]*>(.*?)</script>', html, re.I | re.S)
    if not match:
        return {}
    try:
        variants = json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return {}
    return {
        str(item.get("variant_name", "")).strip(): (
            str(item.get("style_number", "")).strip(),
            urljoin(BASE_URL, "/product/" + str(item.get("url", "")).strip().lstrip("/")),
        )
        for item in variants
        if isinstance(item, dict) and item.get("variant_name") and item.get("style_number")
    }


def _variant_sku_map(html: str) -> dict[str, str]:
    """Compatibility helper for tests and callers needing SKU only."""
    return {name: details[0] for name, details in _variant_details(html).items()}

def _api_quote(page, sku: str, color: str, finger_size: str, metal: str, finish: str, quality: str) -> tuple[str, str]:
    """Get the account-specific price from the site's configuration endpoint.

    Visible controls discover valid choices and color media only. This request,
    made through the authenticated browser context, is the price source of truth.
    """
    params = {
        "style_number": sku, "color": color,
        "quantity": "1", "metal": metal, "level": finish, "quality": quality, "format": "json",
    }
    if finger_size:
        params["finger_size"] = f"{float(finger_size):.2f}"
    response = page.context.request.get(urljoin(BASE_URL, "/api/calculate-price-due-date/") + "?" + urlencode(params), timeout=90_000)
    if not response.ok:
        return "", f"price_api_http_{response.status}"
    try:
        payload = response.json()
    except Exception:
        return "", "price_api_invalid_json"
    price = payload.get("price") if isinstance(payload, dict) else None
    if price is None:
        detail = payload.get("error") if isinstance(payload, dict) else ""
        return "", f"price_api_no_price{':' + str(detail) if detail else ''}"
    try:
        return f"${float(price):,.2f}", ""
    except (TypeError, ValueError):
        return "", "price_api_invalid_price"


def _configuration_url(base_url: str, sku: str, color: str, finger_size: str, metal: str, finish: str, quality: str) -> str:
    parts = urlsplit(base_url)
    params = {"style_number": sku, "color": color, "metal": metal, "level": finish, "quality": quality}
    if finger_size:
        params["finger_size"] = f"{float(finger_size):.2f}"
    query = urlencode(params)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))

def _trigger(page, options_id: str):
    return page.locator(f'[aria-controls="{options_id}"]:visible')


def _options(page, options_id: str) -> list[str]:
    trigger = _trigger(page, options_id)
    if trigger.count() == 0:
        return [""]
    page.keyboard.press("Escape")
    trigger.click(force=True)
    values = page.locator(f'#{options_id} [property-value]').evaluate_all(
        "els => [...new Set(els.map(e => e.getAttribute('property-value')).filter(Boolean))]"
    )
    page.keyboard.press("Escape")
    return values or [""]


def _choose(page, options_id: str, value: str) -> None:
    if not value:
        return
    trigger = _trigger(page, options_id)
    if trigger.count() == 0:
        raise ValueError(f"Visible control unavailable: {options_id}")
    page.keyboard.press("Escape")
    trigger.click(force=True)
    option = page.locator(f'#{options_id} [property-value]').filter(has_text=value).first
    if option.count() == 0:
        raise ValueError(f"Option no longer available: {options_id}={value}")
    option.click(force=True)
    page.wait_for_timeout(350)

def _choose_color(page, color: str) -> None:
    page.keyboard.press("Escape")
    page.locator(f'.color-option[data-value="{color}"]:visible').click(force=True)
    page.wait_for_timeout(350)


def _finger_sizes(page) -> list[str]:
    """Client-selected standard size for all ring pricing configurations."""
    field = page.locator("#finger-size-input:visible")
    if field.count() == 0:
        return [""]
    minimum, maximum = field.get_attribute("min"), field.get_attribute("max")
    if minimum and maximum and not (float(minimum) <= 7 <= float(maximum)):
        return []
    return ["7"]

def _choose_finger_size(page, value: str) -> None:
    if not value:
        return
    field = page.locator("#finger-size-input:visible")
    if field.count():
        field.fill(value)
        field.press("Tab")
        page.wait_for_timeout(350)
        return
    _choose(page, "finger-size-options", value)


def _variant_from_page(page, fallback: str) -> str:
    locator = page.locator("#size-value:visible")
    return locator.inner_text().strip() if locator.count() else fallback

def _selected_value(page, selector: str) -> str:
    locator = page.locator(f"{selector}:visible")
    return locator.inner_text().strip() if locator.count() else ""


def _live_configuration(page) -> dict[str, str]:
    selected_color = page.locator(".color-option.is-selected:visible").evaluate_all("els => els[0]?.dataset.value || ''")
    return {
        "variant": _selected_value(page, "#size-value"),
        "finger_size": page.locator("#finger-size-input:visible").input_value().strip() if page.locator("#finger-size-input:visible").count() else "",
        "metal": _selected_value(page, "#metal-value"),
        "color": selected_color,
        "finish": _selected_value(page, "#level-value"),
        "quality": _selected_value(page, "#quality-value"),
    }

def _sku_from_page(page, fallback: str) -> str:
    locator = page.locator("#product-style-number:visible")
    return locator.inner_text().strip() if locator.count() else fallback


def capture_product_configurations(page, product_url: str, category: str, max_rows: int | None = None) -> list[FullSiteProduct]:
    """Capture every visible, valid purchasable configuration without cart actions."""
    _goto(page, product_url)
    variant_details = _variant_details(page.content())
    variants = _options(page, "size-options")
    rows: list[FullSiteProduct] = []
    for variant in variants:
        _choose(page, "size-options", variant)
        for finger_size in _finger_sizes(page):
            _choose_finger_size(page, finger_size)
            metals = _options(page, "metal-options")
            for metal in metals:
                _choose(page, "metal-options", metal)
                colors = page.locator(".color-option[data-value]:visible").evaluate_all(
                    "els => [...new Set(els.map(e => e.dataset.value))]"
                ) or [""]
                for color in colors:
                    if color:
                        _choose_color(page, color)
                    finishes = _options(page, "level-options")
                    finish = "Complete" if "Complete" in finishes else next((v for v in finishes if v.casefold() == "semi-mount"), "")
                    if not finish:
                        continue
                    _choose(page, "level-options", finish)
                    for quality in _options(page, "quality-options"):
                        try:
                            _choose(page, "quality-options", quality)
                        except ValueError:
                            continue
                        live = _live_configuration(page)
                        intended = {"variant": variant, "finger_size": finger_size, "metal": metal, "color": color, "finish": finish, "quality": quality}
                        base = product_from_html(page.url, category, page.content())
                        variant_sku, variant_url = variant_details.get(
                            variant, (_sku_from_page(page, base.sku), page.url)
                        )
                        quote_price, quote_error = _api_quote(page, variant_sku, color, finger_size, metal, finish, quality)
                        base.product_url = _configuration_url(variant_url, variant_sku, color, finger_size, metal, finish, quality)
                        mismatch = [name for name, value in intended.items() if value and live.get(name) != value]
                        rows.append(replace(
                            base, sku=variant_sku, price=quote_price, selected_finish=finish,
                            metal_type=metal, metal_color=color, diamond_quality=quality,
                            finger_size=finger_size, variant=variant,
                            error=base.error or quote_error or ("price_not_calculated" if not quote_price else ""),
                        ))
                        if max_rows is not None and len(rows) >= max_rows:
                            return rows
    return rows


def browser_capture_configuration_sample(profile_dir: Path, output_path: Path, evidence_path: Path, product_url: str, max_rows: int | None = None) -> dict[str, object]:
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(str(profile_dir.resolve()), headless=False, viewport={"width": 1440, "height": 1000})
        page = context.pages[0] if context.pages else context.new_page()
        products = capture_product_configurations(page, product_url, "Wedding Bands", max_rows=max_rows)
        export_fullsite_workbook(products, output_path)
        evidence = {
            "product_url": product_url, "configuration_rows": len(products),
            "priced_rows": sum(bool(product.price) for product in products),
            "errors": [product.error for product in products if product.error], "sample_workbook": str(output_path),
        }
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        context.close()
        return evidence

















