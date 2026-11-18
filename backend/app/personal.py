"""Personal wardrobe, explicit inspiration, and durable dismissal boundaries."""
import json
from . import db
from .intelligence import norm

def identity(p):
    # Merchant/price-independent identity; unknown variants remain distinct when supplied.
    parts=[p.get('gtin') or '',p.get('brand') or '',p.get('model_number') or p.get('title') or p['id'],','.join(sorted(p.get('colors',[]))),p.get('size') or '']
    return '|'.join(norm(x) for x in parts)

def context(user):
    p=json.loads(user['preferences'])
    with db.connect() as conn:
        rows=conn.execute("SELECT p.data FROM swipes s JOIN products p ON p.id=s.product_id WHERE s.user_id=? AND s.action='dislike'",(user['id'],)).fetchall()
    p['_dismissed_keys']=list({identity(json.loads(r[0])) for r in rows})
    # Inspiration tags are explicitly selected by the user; no celebrity endorsement is inferred.
    p['aesthetics']=list(dict.fromkeys(p.get('aesthetics',[])+[tag for item in p.get('inspirations',[]) for tag in item.get('tags',[])]))
    return p

def visible(preferences,items):
    keys=set(preferences.get('_dismissed_keys',[]))
    return [p for p in items if identity(p) not in keys]
