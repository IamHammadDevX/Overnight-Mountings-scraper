from __future__ import annotations
from dataclasses import dataclass
from time import sleep
from urllib.parse import urljoin
import requests
from .media import parse_color_media, with_color
from .models import ColorMedia, LookupOutcome

BASE_URL = "https://www.overnightmountings.com"
TRANSIENT_STATUS = {408, 425, 429, 500, 502, 503, 504}

@dataclass
class PageResponse:
    outcome: LookupOutcome
    url: str
    html: str | None = None
    detail: str | None = None

class OvernightClient:
    def __init__(self, timeout_seconds: float = 30, retries: int = 3, session: requests.Session | None = None):
        self.timeout_seconds, self.retries = timeout_seconds, retries
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", "OvernightMediaAudit/0.1")

    def _get(self, url: str, **kwargs) -> requests.Response | PageResponse:
        for number in range(self.retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout_seconds, **kwargs)
            except requests.RequestException as error:
                if number < self.retries:
                    sleep(min(2 ** number, 8)); continue
                return PageResponse(LookupOutcome.TRANSIENT_ERROR, url, detail=str(error))
            if response.status_code in TRANSIENT_STATUS and number < self.retries:
                sleep(min(2 ** number, 8)); continue
            return response
        raise AssertionError("unreachable")

    def resolve_sku(self, sku: str) -> PageResponse:
        response = self._get(urljoin(BASE_URL, "/api/search_suggestions/"), params={"q": sku})
        if isinstance(response, PageResponse): return response
        if response.status_code in TRANSIENT_STATUS: return PageResponse(LookupOutcome.TRANSIENT_ERROR, response.url, detail=f"HTTP {response.status_code}")
        if not response.ok: return PageResponse(LookupOutcome.PERMANENT_ERROR, response.url, detail=f"HTTP {response.status_code}")
        try: products = response.json().get("products", [])
        except ValueError as error: return PageResponse(LookupOutcome.PERMANENT_ERROR, response.url, detail=f"Invalid search JSON: {error}")
        exact = next((item for item in products if str(item.get("style_number", "")).casefold() == sku.casefold()), None)
        if exact is None or not exact.get("url"): return PageResponse(LookupOutcome.NOT_FOUND, response.url, detail="No exact SKU in search response")
        return PageResponse(LookupOutcome.FOUND, urljoin(BASE_URL + "/product/", str(exact["url"])))

    def get_page(self, url: str) -> PageResponse:
        response = self._get(url)
        if isinstance(response, PageResponse): return response
        if response.status_code == 404: return PageResponse(LookupOutcome.NOT_FOUND, response.url, detail="HTTP 404")
        if response.status_code in TRANSIENT_STATUS: return PageResponse(LookupOutcome.TRANSIENT_ERROR, response.url, detail=f"HTTP {response.status_code}")
        return PageResponse(LookupOutcome.FOUND, response.url, html=response.text) if response.ok else PageResponse(LookupOutcome.PERMANENT_ERROR, response.url, detail=f"HTTP {response.status_code}")

    def capture_color(self, product_url: str, color: str) -> tuple[PageResponse, ColorMedia | None]:
        page = self.get_page(with_color(product_url, color))
        if page.outcome is not LookupOutcome.FOUND: return page, None
        try: return page, parse_color_media(page.html or "", color)
        except ValueError as error: return PageResponse(LookupOutcome.PERMANENT_ERROR, page.url, detail=str(error)), None


