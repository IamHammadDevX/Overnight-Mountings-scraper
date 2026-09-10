from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def now() -> str: return datetime.now(timezone.utc).isoformat()
def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con=sqlite3.connect(path); con.row_factory=sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL"); return con

def init(con: sqlite3.Connection) -> None:
    con.executescript("""
    CREATE TABLE IF NOT EXISTS products (url TEXT PRIMARY KEY, category TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0, started_at TEXT, completed_at TEXT, error TEXT);
    CREATE TABLE IF NOT EXISTS rows (id INTEGER PRIMARY KEY, product_url TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    """); con.commit()
def set_meta(con, key, value): con.execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(key,str(value))); con.commit()
def get_meta(con,key,default=''): 
    r=con.execute('SELECT value FROM meta WHERE key=?',(key,)).fetchone(); return r['value'] if r else default
def add_products(con, products):
    con.executemany("INSERT OR IGNORE INTO products(url,category) VALUES(?,?)",products); con.commit()
def claim(con):
    row=con.execute("SELECT url,category FROM products WHERE status IN ('pending','failed') ORDER BY url LIMIT 1").fetchone()
    if not row:return None
    con.execute("UPDATE products SET status='running',attempts=attempts+1,started_at=?,error='' WHERE url=?",(now(),row['url']));con.commit();return row
def finish(con,url,payloads):
    import json
    con.execute('DELETE FROM rows WHERE product_url=?',(url,))
    con.executemany('INSERT INTO rows(product_url,payload,created_at) VALUES(?,?,?)',[(url,json.dumps(x),now()) for x in payloads])
    con.execute("UPDATE products SET status='complete',completed_at=? WHERE url=?",(now(),url));con.commit()
def fail(con,url,error): con.execute("UPDATE products SET status='failed',error=? WHERE url=?",(error[:1000],url));con.commit()
def status(con):
    counts={r['status']:r['n'] for r in con.execute('SELECT status,count(*) n FROM products GROUP BY status')}; total=sum(counts.values()); done=counts.get('complete',0); start=get_meta(con,'started_at');
    return {'total_products':total,'complete':done,'pending':counts.get('pending',0),'running':counts.get('running',0),'failed':counts.get('failed',0),'rows':con.execute('SELECT count(*) FROM rows').fetchone()[0],'started_at':start}
