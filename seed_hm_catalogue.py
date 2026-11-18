"""Seed the team backend's catalogue with the H&M India listing snapshot in ./products.

Why: the backend ships 10 fictional fixtures with no prices or photos. The files in ./products are real H&M India
listings (names and INR prices observed on hm.com on 2026-11-18, photos from the listing). This inserts them as
non-demo products so the swipe deck, saved list, daily stylist and outfit completion work on real-looking data.

Honesty rules kept (see docs/BACKEND_BLUEPRINT.md section 10):
  * price/brand/merchant come from the listing; merchant_url, gtin, model_number and size stay null (never invented);
  * colours come from the photo (nearest named colour); fits come only from words in the listing title;
  * aesthetics/weather_tags are curated rules by garment type, so source is 'hm_in_listing_snapshot', not live data;
  * image_url is a path served by the Alluré web server (/products/<file>).

Usage (backend stopped or running; SQLite WAL is safe):
    python3 seed_hm_catalogue.py --db backend/runtime/stylematch.sqlite3
Needs Pillow (already in backend/requirements.txt). Re-running updates the same rows.
"""
import argparse, hashlib, json, re, sqlite3, urllib.parse
from pathlib import Path
from PIL import Image

NAMED = {  # backend colour vocabulary -> reference RGB
    'black': (24, 24, 27), 'white': (250, 250, 250), 'grey': (138, 141, 145), 'beige': (214, 196, 166), 'cream': (241, 233, 216),
    'brown': (109, 76, 53), 'olive': (107, 107, 58), 'green': (47, 93, 70), 'navy': (34, 48, 79), 'blue': (59, 91, 140),
    'red': (192, 57, 43), 'burgundy': (110, 31, 44), 'pink': (232, 180, 176), 'yellow': (216, 164, 44), 'orange': (196, 104, 63), 'purple': (150, 120, 190),
}
CATEGORY = {'tee': 'tops', 'shirt': 'tops', 'hoodie': 'tops', 'jacket': 'tops', 'kurta': 'tops', 'trousers': 'bottoms', 'skirt': 'bottoms',
            'dress': 'one-pieces', 'shoes': 'footwear', 'bag': 'accessories', 'watch': 'accessories', 'cap': 'accessories', 'sunglasses': 'accessories'}
AESTHETICS = {'tee': ['casual', 'minimalist'], 'shirt': ['smart_casual', 'classic'], 'hoodie': ['streetwear', 'casual'], 'jacket': ['outdoor', 'streetwear'],
              'trousers': ['casual', 'minimalist'], 'skirt': ['classic'], 'dress': ['classic', 'smart_casual'], 'shoes': ['casual'], 'bag': ['minimalist'],
              'cap': ['streetwear'], 'sunglasses': ['classic']}
WEATHER = {'tee': ['warm', 'hot'], 'shirt': ['mild', 'warm'], 'hoodie': ['cold', 'mild'], 'jacket': ['cold', 'mild'], 'trousers': ['mild', 'cold'], 'skirt': ['warm', 'mild'],
           'dress': ['warm', 'mild'], 'shoes': ['mild'], 'bag': ['mild'], 'cap': ['warm', 'mild'], 'sunglasses': ['warm', 'hot']}


def dominant(path):
    img = Image.open(path).convert('RGB').resize((40, 40))
    px = [img.getpixel((x, y)) for x in range(8, 32) for y in range(12, 32)]  # central torso band
    def keep(p):
        r, g, b = p; mx, mn = max(p), min(p); sat = 0 if mx == 0 else (mx - mn) / mx
        skin = r > g > b and 0.2 < sat < 0.6 and r > 95 and mx - mn > 15 and r - b > 25
        return not (skin or (sat < 0.12 and mx > 215))  # drop skin and light studio background
    px = [p for p in px if keep(p)] or px
    return tuple(sum(c) / len(px) for c in zip(*px))


def nearest(rgb):
    return min(NAMED, key=lambda n: sum((a - b) ** 2 for a, b in zip(NAMED[n], rgb)))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--db', required=True); ap.add_argument('--products', default=str(Path(__file__).parent / 'products'))
    a = ap.parse_args(); db = sqlite3.connect(a.db); n = 0
    db.execute('CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
    for f in sorted(Path(a.products).iterdir()):
        if f.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp'): continue
        parts = [s.strip() for s in f.stem.split('__')]
        if len(parts) < 4 or parts[1] not in CATEGORY: print('skip', f.name); continue
        title, typ, price, brand = parts[0], parts[1], float(parts[2]), parts[3]
        low = title.lower()
        fits = [w for w in ('relaxed', 'loose', 'oversized', 'slim', 'regular', 'straight') if w in low]
        fits = ['relaxed' if w == 'loose' else w for w in fits]
        functional = ['water_resistant'] if 'water-repellent' in low or 'rain' in low else []
        weather = WEATHER[typ] + (['rain'] if functional else [])
        p = dict(id='hm-' + re.sub(r'[^a-z0-9]+', '-', low).strip('-') + '-' + hashlib.sha1(f.name.encode()).hexdigest()[:6],
                 title=title, brand=brand, category=CATEGORY[typ], colors=[nearest(dominant(f))], aesthetics=AESTHETICS[typ], fits=fits, weather_tags=weather,
                 functional_tags=functional, size=None, model_number=None, gtin=None, price=price, shipping_cost=None, currency='INR',
                 image_url='/products/' + urllib.parse.quote(f.name), merchant_url=None, merchant=brand, source='hm_in_listing_snapshot', is_demo=False,
                 observed_at='2026-11-18T00:00:00+00:00')
        db.execute('INSERT INTO products VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data', (p['id'], json.dumps(p))); n += 1
    db.commit(); print(f'seeded {n} products into {a.db}')


if __name__ == '__main__':
    main()
