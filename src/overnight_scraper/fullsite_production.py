from __future__ import annotations
import json, os
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from .browser import capture_product_configurations
from .fullsite import BASE_URL, DEFAULT_CATALOG_SEEDS, FullSiteProduct, export_fullsite_workbook, extract_links
from .fullsite_store import connect, init, set_meta, get_meta, add_products, claim, finish, fail, status as db_status, now

def _login(page, username_env: str, password_env: str) -> None:
    page.goto(f"{BASE_URL}/account/login/", wait_until="domcontentloaded", timeout=90_000)
    if not page.locator('input[name="username"]').count(): return
    username, password = os.environ.get(username_env), os.environ.get(password_env)
    if not username or not password: raise RuntimeError("Missing server login environment variables")
    page.locator('input[name="username"]').fill(username)
    page.locator('input[name="password"]').fill(password)
    page.locator('button[type="submit"], input[type="submit"]').first.click()
    page.wait_for_timeout(2_000)
    if '/account/login' in page.url: raise RuntimeError("Browser login failed or requires manual review")

def _category(url: str) -> str:
    part=next((x for x in urlsplit(url).path.split('/') if x), 'Catalog')
    return part.replace('_',' ').title()

def _discover_browser(page, db: Path) -> int:
    con=connect(db); init(con)
    if get_meta(con,'discovered_at'): return db_status(con)['total_products']
    queue=[f"{BASE_URL}{seed}" for seed in DEFAULT_CATALOG_SEEDS]; visited=set(); found=[]
    while queue:
        url=queue.pop(0)
        if url in visited: continue
        visited.add(url)
        try:
            page.goto(url,wait_until='domcontentloaded',timeout=90_000); page.wait_for_timeout(500)
            products, more=extract_links(page.content(),page.url)
            found.extend((item,_category(page.url)) for item in products)
            queue.extend(sorted(x for x in more if x not in visited and x not in queue))
        except Exception: continue
    add_products(con,found); set_meta(con,'discovered_at',now()); set_meta(con,'started_at',now()); return db_status(con)['total_products']

def run(db: Path, profile: Path, username_env: str, password_env: str, output: Path, limit: int|None=None) -> int:
    con=connect(db); init(con); processed=0
    with sync_playwright() as pw:
      ctx=pw.chromium.launch_persistent_context(str(profile),headless=True)
      page=ctx.pages[0] if ctx.pages else ctx.new_page()
      _login(page,username_env,password_env)
      _discover_browser(page,db)
      while limit is None or processed<limit:
        task=claim(con)
        if not task: break
        try:
          rows=capture_product_configurations(page,task['url'],task['category'])
          finish(con,task['url'],[asdict(row) for row in rows]); processed+=1
        except Exception as e: fail(con,task['url'],f'{type(e).__name__}: {e}')
      ctx.close()
    export(db,output); return processed

def export(db:Path,output:Path)->None:
    con=connect(db); init(con); rows=[]
    for r in con.execute('SELECT payload FROM rows ORDER BY product_url,id'): rows.append(FullSiteProduct(**json.loads(r['payload'])))
    export_fullsite_workbook(rows,output)
def report(db:Path)->dict:
    con=connect(db);init(con);return db_status(con)
