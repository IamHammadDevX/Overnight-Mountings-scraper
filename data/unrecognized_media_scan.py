import json
from pathlib import Path
from overnight_scraper.http import OvernightClient
from overnight_scraper.media import parse_color_media, unrecognized_color_media
from overnight_scraper.workbooks import load_families
client = OvernightClient()
records = []
for family in load_families(Path('Overnight_Unique_SKUs_For_Scraping.xlsx'))[:250]:
    resolved = client.resolve_sku(family.representative_sku)
    if resolved.outcome.value != 'found':
        records.append({'family_id':family.family_id,'sku':family.representative_sku,'outcome':resolved.outcome.value,'unrecognized_color_media':[]}); continue
    page = client.get_page(resolved.url)
    unknown = unrecognized_color_media(page.html) if page.html else []
    records.append({'family_id':family.family_id,'sku':family.representative_sku,'outcome':page.outcome.value,'unrecognized_color_media':unknown})
summary = {'families_scanned':len(records),'families_with_unrecognized_color_media':sum(bool(x['unrecognized_color_media']) for x in records),'unrecognized_url_count':sum(len(x['unrecognized_color_media']) for x in records),'records':records}
Path('data/unrecognized_media_scan_250.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='records'}))
