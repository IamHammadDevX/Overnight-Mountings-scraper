from pathlib import Path
import json, re
from overnight_scraper.http import OvernightClient
from overnight_scraper.media import _raw_media, page_supports_color
skus = ["10002-10X8", "10005-1", "1/2-AS-.10S10"]
client = OvernightClient()
audit = []
for sku in skus:
    resolved = client.resolve_sku(sku)
    page = client.get_page(resolved.url) if resolved.html is None and resolved.outcome.value == "found" else resolved
    html = page.html or ""
    images, videos = _raw_media(html)
    scripts = re.findall(r'<script[^>]+(?:id=["\']([^"\']+)["\'])?[^>]*type=["\']application/json["\']', html, re.I)
    audit.append({"sku": sku, "product_url": page.url, "html_bytes": len(html), "yellow_literal_count": html.lower().count("yellow"), "rose_literal_count": html.lower().count("rose"), "data_color_count": html.lower().count("data-color"), "image_tag_count": len(re.findall(r'<img\\b', html, re.I)), "application_json_ids": scripts, "supports_yellow": page_supports_color(html, "Yellow"), "supports_rose": page_supports_color(html, "Rose"), "product_images": images, "product_videos": videos, "color_marked_images": [u for u in images if any(t in u.lower() for t in ('.alt', '.yellow', '.rose'))], "color_marked_videos": [u for u in videos if any(t in u.lower() for t in ('.yellow', '.rose', '.white'))]})
Path('data/static_media_audit.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
for item in audit: print(item['sku'], 'images',len(item['product_images']),'videos',len(item['product_videos']),'color-marked',len(item['color_marked_images']),len(item['color_marked_videos']),'swatches',item['supports_yellow'],item['supports_rose'])
