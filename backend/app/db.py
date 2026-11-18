import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from .config import settings

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, token_hash TEXT UNIQUE NOT NULL, name TEXT NOT NULL, preferences TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS swipes (id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), product_id TEXT NOT NULL REFERENCES products(id), action TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS swipes_user ON swipes(user_id, created_at);
CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), kind TEXT NOT NULL, status TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS jobs_user ON jobs(user_id, kind, created_at);
CREATE TABLE IF NOT EXISTS agent_runs (id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), data TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS idempotency (user_id TEXT NOT NULL, key TEXT NOT NULL, kind TEXT NOT NULL, result_id TEXT NOT NULL, PRIMARY KEY(user_id,key,kind));
PRAGMA user_version=1;
'''

def now():
    return datetime.now(timezone.utc).isoformat()

@contextmanager
def connect():
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(settings.database_path, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA journal_mode=WAL')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def initialize():
    with connect() as db:
        db.executescript(SCHEMA)
        for product in seed_products():
            db.execute('INSERT OR IGNORE INTO products VALUES (?,?)', (product['id'], json.dumps(product)))

def seed_products():
    # Fictional, explicitly labelled fixtures. Never merchant offers.
    rows = [
        ('neutral-shirt','Relaxed neutral shirt','tops',['beige'],['minimalist'],['relaxed'],['warm','mild'],[]),
        ('rain-shell','Lightweight rain shell','tops',['olive'],['outdoor','minimalist'],['relaxed'],['rain','mild'],['water_resistant']),
        ('dark-trousers','Straight dark trousers','bottoms',['black'],['minimalist','smart_casual'],['straight'],['mild','rain'],[]),
        ('white-sneakers','Clean white sneakers','footwear',['white'],['minimalist','streetwear'],['regular'],['warm','mild'],[]),
        ('rain-boots','Water-resistant ankle boots','footwear',['black'],['outdoor'],['regular'],['rain','cold'],['water_resistant']),
        ('linen-shirt','Airy linen shirt','tops',['white'],['minimalist'],['relaxed'],['hot','warm'],['breathable']),
        ('wool-knit','Warm textured knit','tops',['navy'],['smart_casual'],['regular'],['cold'],['insulating']),
        ('graphic-tee','Graphic oversized tee','tops',['red'],['streetwear'],['oversized'],['warm','hot'],[]),
        ('relaxed-jeans','Relaxed blue jeans','bottoms',['blue'],['streetwear'],['relaxed'],['mild','cold'],[]),
        ('neutral-shorts','Relaxed neutral shorts','bottoms',['beige'],['casual'],['relaxed'],['hot','warm'],[]),
    ]
    return [dict(id=r[0],title=r[1],category=r[2],colors=r[3],aesthetics=r[4],fits=r[5],weather_tags=r[6],functional_tags=r[7],price=None,currency='INR',brand=None,size=None,model_number=None,gtin=None,shipping_cost=None,image_url=None,merchant_url=None,merchant=None,source='demo_catalogue',is_demo=True,observed_at=None) for r in rows]

def products():
    with connect() as db:
        return [json.loads(row['data']) for row in db.execute('SELECT data FROM products')]

def save_products(items):
    with connect() as db:
        for p in items:
            db.execute('INSERT INTO products VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data', (p['id'],json.dumps(p)))

def get_job(job_id, user_id):
    with connect() as db:
        row=db.execute('SELECT * FROM jobs WHERE id=? AND user_id=?',(job_id,user_id)).fetchone()
        return dict(row) if row else None

def update_job(job_id,status,data):
    with connect() as db:
        db.execute('UPDATE jobs SET status=?,data=?,updated_at=? WHERE id=?',(status,json.dumps(data),now(),job_id))
