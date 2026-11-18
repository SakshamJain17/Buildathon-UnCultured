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

def feedback(user,product_id,action,idempotency_key=None):
    import uuid
    from .intelligence import adapt
    from .providers import ProviderError
    if action not in {'like','dislike','save'}:raise ValueError('Unsupported feedback action')
    with db.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        if idempotency_key:
            old=conn.execute("SELECT result_id FROM idempotency WHERE user_id=? AND key=? AND kind='swipe'",(user['id'],idempotency_key)).fetchone()
            if old:return {'swipe_id':old[0],'replayed':True}
        row=conn.execute('SELECT data FROM products WHERE id=?',(product_id,)).fetchone()
        if not row:raise ProviderError('NOT_FOUND','Unknown catalogue product.',404)
        prefs=json.loads(conn.execute('SELECT preferences FROM users WHERE id=?',(user['id'],)).fetchone()[0])
        prefs=adapt(prefs,json.loads(row[0]),action)
        swipe_id='swp_'+uuid.uuid4().hex
        conn.execute('UPDATE users SET preferences=? WHERE id=?',(json.dumps(prefs),user['id']))
        conn.execute('INSERT INTO swipes VALUES (?,?,?,?,?)',(swipe_id,user['id'],product_id,action,db.now()))
        if idempotency_key:conn.execute('INSERT INTO idempotency VALUES (?,?,?,?)',(user['id'],idempotency_key,'swipe',swipe_id))
    return {'swipe_id':swipe_id,'action':action,'product_id':product_id,'preferences':prefs}

def patch_preferences(user,patch):
    from .schemas import Preferences
    allowed=set(Preferences.model_fields)
    if not set(patch)<=allowed:raise ValueError('Unsupported preference field')
    # Validate partial values, then update only fields actually supplied.
    validated=Preferences.model_validate(patch).model_dump(include=set(patch))
    with db.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        prefs=json.loads(conn.execute('SELECT preferences FROM users WHERE id=?',(user['id'],)).fetchone()[0])
        prefs.update(validated)
        conn.execute('UPDATE users SET preferences=? WHERE id=?',(json.dumps(prefs),user['id']))
    return prefs

def progress(user):
    with db.connect() as conn:
        counts={r[0]:r[1] for r in conn.execute('SELECT action,count(*) FROM swipes WHERE user_id=? GROUP BY action',(user['id'],))}
        wardrobe_count=conn.execute('SELECT count(*) FROM wardrobe WHERE user_id=?',(user['id'],)).fetchone()[0]
    return {'likes':counts.get('like',0),'saved':counts.get('save',0),'dismissed':counts.get('dislike',0),'wardrobe_count':wardrobe_count}
