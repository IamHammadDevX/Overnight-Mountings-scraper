from __future__ import annotations
import json
import re
from html import unescape
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from .models import ColorMedia

_SCRIPT = re.compile(r'<script[^>]+id=["\'](?P<id>product-(?:images|videos))["\'][^>]*>(?P<body>.*?)</script>', re.I | re.S)
_COLORS = re.compile(r'availableColors\s*=\s*filterColorOptions\((?P<colors>\[[^\]]*\])\)', re.S)
_YELLOW_IMAGE = re.compile(r'\.(?:side\.|set\.)?alt\.(?:jpe?g|png|webp)(?:\?.*)?$', re.I)
_ROSE_IMAGE = re.compile(r'\.(?:side\.|set\.)?alt1\.(?:jpe?g|png|webp)(?:\?.*)?$', re.I)
_YELLOW_VIDEO = re.compile(r'\.video\.yellow\.mp4(?:\?.*)?$', re.I)
_ROSE_VIDEO = re.compile(r'\.video\.rose\.mp4(?:\?.*)?$', re.I)
_WHITE_VIDEO = re.compile(r'\.video\.white\.mp4(?:\?.*)?$', re.I)

def _raw_media(html: str) -> tuple[list[str], list[str]]:
    values: dict[str, list[str]] = {"product-images": [], "product-videos": []}; found = set()
    for match in _SCRIPT.finditer(html):
        found.add(match.group("id")); data = json.loads(unescape(match.group("body")).strip())
        if not isinstance(data, list) or not all(isinstance(url, str) for url in data): raise ValueError(f"Unexpected {match.group('id')} JSON shape")
        values[match.group("id")] = data
    if not found: raise ValueError("Product media scripts absent from page")
    return values["product-images"], values["product-videos"]

def page_supports_color(html: str, color: str) -> bool | None:
    match = _COLORS.search(html)
    if not match: return None
    try: return color in json.loads(match.group("colors"))
    except json.JSONDecodeError: return None

def unrecognized_color_media(html: str) -> list[str]:
    images, _ = _raw_media(html)
    return [url for url in images if ".alt" in url.lower() and not _YELLOW_IMAGE.search(url) and not _ROSE_IMAGE.search(url)]

def parse_color_media(html: str, color: str = "White") -> ColorMedia:
    """Use explicit media suffix whitelist; unknown alternates are never assigned."""
    supported = page_supports_color(html, color)
    if supported is False: return ColorMedia(available=False, evidence={"source": "availableColors"})
    images, videos = _raw_media(html)
    images = [url for url in images if ".cat" not in url.lower()]
    if color == "Yellow":
        images, videos = [u for u in images if _YELLOW_IMAGE.search(u)], [u for u in videos if _YELLOW_VIDEO.search(u)]
    elif color == "Rose":
        images, videos = [u for u in images if _ROSE_IMAGE.search(u)], [u for u in videos if _ROSE_VIDEO.search(u)]
    elif color == "White":
        images, videos = [u for u in images if ".alt" not in u.lower()], [u for u in videos if _WHITE_VIDEO.search(u) or (".yellow" not in u.lower() and ".rose" not in u.lower())]
    else: raise ValueError(f"Unsupported color: {color}")
    return ColorMedia(images, videos, True, {"source": "structured_scripts", "color_specific": bool(images or videos), "color_swatch": supported})

def with_color(url: str, color: str) -> str:
    parts = urlsplit(url); query = dict(parse_qsl(parts.query, keep_blank_values=True)); query["color"] = color
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
