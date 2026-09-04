import json
from pathlib import Path
import openpyxl
from overnight_scraper.http import OvernightClient
from overnight_scraper.media import _raw_media

book = openpyxl.load_workbook('Overnight_Unique_SKUs_For_Scraping.xlsx', read_only=True, data_only=False)
sheet = book['Families To Scrape']
rows = [r for r in sheet.values if r[0] and r[0] != 'Family ID']
bands = [r for r in rows if r[4] == 'Complete Bands'][:8]
others = []
for category in ('Cluster', 'Pearl', 'Fashion'):
    others.append(next(r for r in rows if r[4] == category and r[10] in ('Partial', 'Has Images+Videos')))
selected = bands + others
client = OvernightClient()
audit = []
for r in selected:
    resolution = client.resolve_sku(r[2])
    page = client.get_page(resolution.url)
    images, videos = _raw_media(page.html or '')
    lower = [u.lower() for u in images]
    audit.append({'family_id':r[0], 'sku':r[2], 'category':r[4], 'status':r[10], 'url':page.url, 'image_count':len(images), 'video_count':len(videos), 'yellow_images':sum('.alt2' in u or ('.alt' in u and '.alt1' not in u and '.alt4' not in u) for u in lower), 'rose_images':sum('.alt1' in u or '.alt4' in u for u in lower), 'yellow_videos':sum('.video.yellow' in u.lower() for u in videos), 'rose_videos':sum('.video.rose' in u.lower() for u in videos), 'yellow_alt_images':[u for u in images if '.alt' in u.lower() and not any(x in u.lower() for x in ('.alt1','.alt2','.alt4'))]})
Path('data/convention_audit.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
for x in audit: print(x['category'],x['sku'],x['image_count'],x['video_count'],x['yellow_images'],x['rose_images'],x['yellow_videos'],x['rose_videos'])


