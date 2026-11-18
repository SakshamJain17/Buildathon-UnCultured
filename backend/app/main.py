import asyncio
import hashlib
import hmac
import json
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime,timezone,timedelta
from typing import Annotated,Literal
from fastapi import FastAPI,Depends,File,Form,Header,Query,Request,UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException
from pydantic import ValidationError
from . import db,intelligence,agent,personal
from .config import settings
from .schemas import SessionIn,Preferences,DailyIn,SwipeIn,SearchIn,MatchIn,OutfitIn,AgentIn,VisionResult
from .providers import ProviderError,gemini
from .images import image_bytes,inline,data_uri
from .jobs import run_tryon,refresh_tryon

tasks=set()
@asynccontextmanager
async def lifespan(app):
    db.initialize()
    with db.connect() as conn:
        rows=conn.execute("SELECT * FROM jobs WHERE status IN ('queued','processing')").fetchall()
        for row in rows:
            data=json.loads(row['data'])
            if not data.get('provider_job_id'):
                data['error']={'code':'SERVER_RESTARTED','message':'Submission interrupted. Input photos were not retained. Please submit again.'}
                db.update_job(row['id'],'failed',data)
    yield
    if tasks:
        await asyncio.gather(*tasks,return_exceptions=True)

app=FastAPI(title='ALLURÉ',version='0.1.0',lifespan=lifespan,description='Fashion intelligence tools, weather-aware personalisation, and virtual try-on. Provider availability is explicit. Session bearer tokens isolate user records.')
app.add_middleware(CORSMiddleware,allow_origins=settings.origins,allow_credentials=False,allow_methods=['GET','POST','PUT','DELETE'],allow_headers=['Authorization','Content-Type','Idempotency-Key'])

@app.middleware('http')
async def request_id(request,call_next):
    request.state.request_id='req_'+uuid.uuid4().hex
    try:
        content_length=int(request.headers.get('content-length','0') or 0)
    except ValueError:
        return error(request,'INVALID_INPUT','Invalid Content-Length header.',400)
    if content_length>45*1024*1024:
        return JSONResponse({'success':False,'error':{'code':'REQUEST_TOO_LARGE','message':'Request must be at most 45 MB.'},'request_id':request.state.request_id},status_code=413)
    response=await call_next(request)
    response.headers['X-Request-ID']=request.state.request_id
    response.headers['Cache-Control']='no-store'
    return response

def ok(request,data): return {'success':True,'data':data,'request_id':request.state.request_id}

def error(request,code,message,status):
    return JSONResponse({'success':False,'error':{'code':code,'message':message},'request_id':getattr(request.state,'request_id','unknown')},status_code=status)

@app.exception_handler(ProviderError)
async def provider_error(request,exc): return error(request,exc.code,exc.message,exc.status)
@app.exception_handler(RequestValidationError)
async def validation_error(request,exc): return error(request,'INVALID_INPUT','Request validation failed. See /docs for the required schema.',422)
@app.exception_handler(HTTPException)
async def http_error(request,exc): return error(request,'HTTP_ERROR',str(exc.detail),exc.status_code)
@app.exception_handler(Exception)
async def unexpected(request,exc): return error(request,'INTERNAL_ERROR','Request could not be completed.',500)

async def current_user(authorization:Annotated[str|None,Header()]=None):
    if not authorization or not authorization.startswith('Bearer '): raise ProviderError('UNAUTHORIZED','Create a session and send its bearer token.',401)
    digest=hashlib.sha256(authorization[7:].encode()).hexdigest()
    with db.connect() as conn:
        row=conn.execute('SELECT * FROM users WHERE token_hash=?',(digest,)).fetchone()
    if not row or datetime.fromisoformat(row['created_at'])<datetime.now(timezone.utc)-timedelta(days=settings.session_days):
        raise ProviderError('UNAUTHORIZED','Session is invalid or expired.',401)
    return dict(row)

User=Annotated[dict,Depends(current_user)]

@app.get('/api/v1/health')
async def health(request:Request):
    return ok(request,{'status':'ok','providers':{'vision':bool(settings.ollama_vision_model) if settings.vision_provider=='ollama' else bool(settings.gemini_api_key and settings.gemini_model),'agent':bool(settings.ollama_model) if settings.llm_provider=='ollama' else bool(settings.gemini_api_key and settings.gemini_model),'llm_provider':settings.llm_provider,'shopping':bool(settings.serpapi_api_key),'tryon':bool(settings.fashn_api_key),'weather':True},'provider_status_meaning':'configured, not a live connectivity test','catalogue':'labelled demo fixtures plus retrieved live listings'})

@app.post('/api/v1/sessions',status_code=201)
async def session(request:Request,body:SessionIn):
    token=secrets.token_urlsafe(32); user_id='usr_'+uuid.uuid4().hex
    with db.connect() as conn:
        conn.execute('INSERT INTO users (id,token_hash,name,created_at) VALUES (?,?,?,?)',(user_id,hashlib.sha256(token.encode()).hexdigest(),body.name.strip(),db.now()))
    return ok(request,{'user_id':user_id,'name':body.name.strip(),'token':token,'expires_in_days':settings.session_days})

@app.get('/api/v1/me')
async def me(request:Request,user:User):
    return ok(request,{'user_id':user['id'],'name':user['name'],'preferences':json.loads(user['preferences'])})

@app.put('/api/v1/me/preferences')
async def preferences(request:Request,body:Preferences,user:User):
    p=json.loads(user['preferences']); p.update(body.model_dump())
    with db.connect() as conn: conn.execute('UPDATE users SET preferences=? WHERE id=?',(json.dumps(p),user['id']))
    return ok(request,p)

@app.get('/api/v1/users/{user_id}/preferences')
async def user_preferences(request:Request,user_id:str,user:User):
    if user_id!=user['id']: raise ProviderError('NOT_FOUND','Profile not found.',404)
    return ok(request,json.loads(user['preferences']))

@app.delete('/api/v1/me',status_code=200)
async def delete_me(request:Request,user:User):
    with db.connect() as conn:
        for table in ('swipes','jobs','agent_runs','idempotency','wardrobe'): conn.execute(f'DELETE FROM {table} WHERE user_id=?',(user['id'],))
        conn.execute('DELETE FROM users WHERE id=?',(user['id'],))
    return ok(request,{'deleted':True,'provider_deletion_note':'This deletes local records; external providers apply their own retention policies.'})

@app.get('/api/v1/locations/search')
async def location_search(request:Request,user:User,q:str=Query(min_length=2,max_length=100)):
    return ok(request,await intelligence.cities(q))

@app.post('/api/v1/stylist/daily')
async def daily(request:Request,body:DailyIn,user:User):
    forecast=await intelligence.weather(body.location.latitude,body.location.longitude)
    with db.connect() as conn: wardrobe=[json.loads(r[0]) for r in conn.execute('SELECT data FROM wardrobe WHERE user_id=?',(user['id'],))]
    return ok(request,intelligence.daily_style(user['name'],personal.context(user),forecast,body.occasion,wardrobe))

@app.post('/api/v1/style/analyze')
async def analyze(request:Request,user:User,images:Annotated[list[UploadFile],File()]):
    if len(images)!=5: raise ProviderError('IMAGE_COUNT','Exactly five outfit references are required.',422)
    raw=[await image_bytes(image) for image in images]
    prompt=('Analyse only clothing in these five reference images. Do not infer age, ethnicity, health, body measurements, attractiveness, or other sensitive traits. '
        'Return one entry per image. Use lowercase aesthetic tags, common colour names, silhouettes and garment categories. '
        'Garment categories should be tops, bottoms, footwear, one-pieces, accessories. Material descriptions are visual guesses, explicitly qualified. '
        'Include ambiguity in uncertainty. These are references, not proof of ownership or personal identity.')
    response=await gemini([{'role':'user','parts':[{'text':prompt}]+[inline(x) for x in raw]}],schema=VisionResult.model_json_schema())
    try:
        result=VisionResult.model_validate_json(''.join(p.get('text','') for p in response.get('parts',[])))
    except (ValidationError,ValueError): raise ProviderError('INVALID_MODEL_OUTPUT','Vision returned an invalid fashion profile.',502)
    from collections import Counter
    consolidated={}
    for field in ('aesthetics','preferred_colors','silhouettes','garment_preferences'):
        counts=Counter(v.strip().lower() for image in result.images for v in set(getattr(image,field)) if v.strip())
        consolidated[field]=[v for v,_ in counts.most_common(12)]
    # Read-modify-write atomically, retaining explicit preferences and learned feedback.
    with db.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        p=json.loads(conn.execute('SELECT preferences FROM users WHERE id=?',(user['id'],)).fetchone()[0])
        p['inferred_profile']=consolidated
        for key,value in consolidated.items():
            if not p.get(key): p[key]=value
        conn.execute('UPDATE users SET preferences=? WHERE id=?',(json.dumps(p),user['id']))
    return ok(request,{'style_profile':consolidated,'per_image':[x.model_dump() for x in result.images],'confidence':None,'source_image_count':5,'aggregation':'frequency across images; explicit saved preferences take precedence','images_stored':False})

@app.get('/api/v1/recommendations')
async def recommendations(request:Request,user:User,limit:int=Query(12,ge=1,le=50),include_seen:bool=False):
    with db.connect() as conn: seen=[r[0] for r in conn.execute('SELECT product_id FROM swipes WHERE user_id=?',(user['id'],))]
    result=intelligence.rank(personal.context(user),db.products(),excluded=[] if include_seen else seen)
    return ok(request,{'items':result[:limit],'mode':'attribute_ranking','demo_items_labelled':True})

@app.post('/api/v1/swipes')
async def swipe(request:Request,body:SwipeIn,user:User,idempotency_key:Annotated[str|None,Header(max_length=120)]=None):
    with db.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        if idempotency_key:
            old=conn.execute("SELECT result_id FROM idempotency WHERE user_id=? AND key=? AND kind='swipe'",(user['id'],idempotency_key)).fetchone()
            if old: return ok(request,{'swipe_id':old[0],'replayed':True})
        row=conn.execute('SELECT data FROM products WHERE id=?',(body.product_id,)).fetchone()
        if not row: raise ProviderError('NOT_FOUND','Unknown product.',404)
        p=json.loads(conn.execute('SELECT preferences FROM users WHERE id=?',(user['id'],)).fetchone()[0])
        p=intelligence.adapt(p,json.loads(row[0]),body.action)
        swipe_id='swp_'+uuid.uuid4().hex
        conn.execute('UPDATE users SET preferences=? WHERE id=?',(json.dumps(p),user['id']))
        conn.execute('INSERT INTO swipes VALUES (?,?,?,?,?)',(swipe_id,user['id'],body.product_id,body.action,db.now()))
        if idempotency_key: conn.execute('INSERT INTO idempotency VALUES (?,?,?,?)',(user['id'],idempotency_key,'swipe',swipe_id))
    return ok(request,{'swipe_id':swipe_id,'action':body.action,'preferences':p})

@app.get('/api/v1/saved')
async def saved(request:Request,user:User):
    with db.connect() as conn:
        rows=conn.execute("SELECT DISTINCT p.data FROM products p JOIN swipes s ON p.id=s.product_id WHERE s.user_id=? AND s.action='save'",(user['id'],)).fetchall()
    return ok(request,{'products':personal.visible(personal.context(user),[json.loads(r[0]) for r in rows])})

@app.post('/api/v1/products/search')
async def search(request:Request,body:SearchIn,user:User):
    result=await intelligence.search(body)
    result['products']=personal.visible(personal.context(user),result['products'])
    return ok(request,result)

@app.post('/api/v1/products/match')
async def match(request:Request,body:MatchIn,user:User):
    return ok(request,{'matches':[intelligence.match(body.target.model_dump(),p.model_dump()) for p in body.candidates]})

@app.post('/api/v1/prices/compare')
async def compare(request:Request,body:MatchIn,user:User):
    return ok(request,intelligence.compare(body.target.model_dump(),[p.model_dump() for p in body.candidates]))

@app.post('/api/v1/outfits/complete')
async def complete(request:Request,body:OutfitIn,user:User):
    p=next((p for p in db.products() if p['id']==body.product_id),None)
    if not p: raise ProviderError('NOT_FOUND','Unknown product.',404)
    return ok(request,intelligence.complete(personal.context(user),p,body.budget))

@app.post('/api/v1/agent/shop')
async def shop(request:Request,body:AgentIn,user:User): return ok(request,await agent.shop(user,body))

@app.get('/api/v1/agent/runs/{run_id}')
async def agent_run(request:Request,run_id:str,user:User):
    with db.connect() as conn: row=conn.execute('SELECT data FROM agent_runs WHERE id=? AND user_id=?',(run_id,user['id'])).fetchone()
    if not row: raise ProviderError('NOT_FOUND','Run not found.',404)
    return ok(request,json.loads(row[0]))

@app.post('/api/v1/tryon',status_code=202)
async def tryon(request:Request,user:User,person_image:Annotated[UploadFile,File()],garment_image:Annotated[UploadFile,File()],consent:Annotated[bool,Form()],category:Annotated[Literal['auto','tops','bottoms','one-pieces'],Form()]='tops',idempotency_key:Annotated[str|None,Header(max_length=120)]=None):
    if not consent: raise ProviderError('CONSENT_REQUIRED','Confirm you have permission to use the photographs for generation.',422)
    if not settings.fashn_api_key: raise ProviderError(message='Configure FASHN_API_KEY for real virtual try-on.')
    person,garment=await image_bytes(person_image),await image_bytes(garment_image)
    with db.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        if idempotency_key:
            row=conn.execute("SELECT result_id FROM idempotency WHERE user_id=? AND key=? AND kind='tryon'",(user['id'],idempotency_key)).fetchone()
            if row: return ok(request,{'job_id':row[0],'replayed':True})
        cutoff=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()
        count=conn.execute("SELECT count(*) FROM jobs WHERE user_id=? AND kind='tryon' AND created_at>?",(user['id'],cutoff)).fetchone()[0]
        if count>=settings.max_tryons_per_hour: raise ProviderError('RATE_LIMITED','Hourly try-on limit reached.',429)
        job_id='try_'+uuid.uuid4().hex
        conn.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?)',(job_id,user['id'],'tryon','queued',json.dumps({'category':category,'provider_job_id':None}),db.now(),db.now()))
        if idempotency_key: conn.execute('INSERT INTO idempotency VALUES (?,?,?,?)',(user['id'],idempotency_key,'tryon',job_id))
    task=asyncio.create_task(run_tryon(job_id,data_uri(person),data_uri(garment),category))
    tasks.add(task); task.add_done_callback(tasks.discard)
    return ok(request,{'job_id':job_id,'status':'queued','poll_after_seconds':3})

@app.get('/api/v1/tryon/{job_id}')
async def tryon_status(request:Request,job_id:str,user:User):
    row=db.get_job(job_id,user['id'])
    if not row: raise ProviderError('NOT_FOUND','Try-on job not found.',404)
    row=await refresh_tryon(row)
    data=json.loads(row['data'])
    data.pop('provider_job_id',None)
    return ok(request,{'job_id':job_id,'status':row['status'],**data,'created_at':row['created_at'],'updated_at':row['updated_at'],'notice':'AI appearance preview; not a guarantee of physical fit or sizing.'})

from .schemas import PaletteIn
@app.post('/api/v1/style/palette')
async def color_palette(request:Request,body:PaletteIn,user:User):
    if not body.consent: raise ProviderError('CONSENT_REQUIRED','Opt in to undertone-based colour suggestions.',422)
    return ok(request,intelligence.palette(body.undertone,body.preference))

from .schemas import InspirationsIn,HairIn
from fastapi.responses import Response

@app.put('/api/v1/me/inspirations')
async def inspirations(request:Request,body:InspirationsIn,user:User):
    with db.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        p=json.loads(conn.execute('SELECT preferences FROM users WHERE id=?',(user['id'],)).fetchone()[0])
        p['inspirations']=[x.model_dump() for x in body.inspirations]
        conn.execute('UPDATE users SET preferences=? WHERE id=?',(json.dumps(p),user['id']))
    return ok(request,{'inspirations':p['inspirations'],'notice':'User-selected style inspiration; no endorsement or live celebrity feed is claimed.'})

@app.post('/api/v1/stylist/hair')
async def hairstyle(request:Request,body:HairIn,user:User):
    prompt=('You are ALLURÉ, a personal stylist. Suggest three practical hairstyle options and maintenance tips based only on these user-provided choices. '
        'Do not infer ethnicity, gender, health or face shape. No medical/scalp advice or claims about celebrity endorsement. '
        'Explain these are suggestions, not guaranteed results. Return concise plain text. Choices: '+body.model_dump_json())
    result=await gemini([{'role':'user','parts':[{'text':prompt}]}])
    return ok(request,{'advice':'\n'.join(p.get('text','') for p in result.get('parts',[]) if not p.get('thought')),'source':'model_generated','photo_analysis':False})

@app.post('/api/v1/wardrobe',status_code=201)
async def wardrobe_add(request:Request,user:User,image:Annotated[UploadFile,File()],title:Annotated[str,Form(min_length=1,max_length=120)],category:Annotated[Literal['tops','bottoms','footwear','one-pieces','accessories'],Form()],color:Annotated[str,Form(max_length=40)]='neutral'):
    raw=await image_bytes(image)
    item_id='ward_'+uuid.uuid4().hex
    p={'id':item_id,'title':title,'category':category,'colors':[color.lower()],'aesthetics':[],'fits':[],'weather_tags':[],'functional_tags':[], 'price':None,'currency':'INR','source':'your_wardrobe','is_demo':False,'image_url':None,'merchant_url':None}
    with db.connect() as conn: conn.execute('INSERT INTO wardrobe VALUES (?,?,?,?,?)',(item_id,user['id'],json.dumps(p),raw,db.now()))
    return ok(request,{'item':p})

@app.get('/api/v1/wardrobe')
async def wardrobe_list(request:Request,user:User):
    with db.connect() as conn: rows=conn.execute('SELECT data FROM wardrobe WHERE user_id=?',(user['id'],)).fetchall()
    return ok(request,{'items':[json.loads(r[0]) for r in rows]})

@app.get('/api/v1/wardrobe/{item_id}/image')
async def wardrobe_image(item_id:str,user:User):
    with db.connect() as conn: row=conn.execute('SELECT image FROM wardrobe WHERE id=? AND user_id=?',(item_id,user['id'])).fetchone()
    if not row: raise ProviderError('NOT_FOUND','Wardrobe image not found.',404)
    return Response(bytes(row[0]),media_type='image/jpeg',headers={'Cache-Control':'no-store'})

@app.delete('/api/v1/wardrobe/{item_id}')
async def wardrobe_delete(request:Request,item_id:str,user:User):
    with db.connect() as conn: result=conn.execute('DELETE FROM wardrobe WHERE id=? AND user_id=?',(item_id,user['id']))
    if not result.rowcount: raise ProviderError('NOT_FOUND','Wardrobe item not found.',404)
    return ok(request,{'deleted':True})

@app.post('/api/v1/wardrobe/outfits')
async def wardrobe_outfits(request:Request,user:User):
    with db.connect() as conn: rows=conn.execute('SELECT data FROM wardrobe WHERE user_id=?',(user['id'],)).fetchall()
    ranked=intelligence.rank(personal.context(user),[json.loads(r[0]) for r in rows])
    selected=[]
    for category in ('tops','bottoms','footwear'):
        match=next((x for x in ranked if x['product'].get('category')==category),None)
        if match: selected.append(match)
    return ok(request,{'items':selected,'notice':'Based on your selected wardrobe attributes; garment vision and full colour compatibility are not applied.'})


@app.get('/api/v1/catalogue')
async def catalogue(request:Request):
    items=[p for p in db.products() if p.get('source')=='reference_catalogue']
    return ok(request,{'products':items,'notice':'User-supplied H&M reference image catalogue. No affiliation, live price or availability is claimed.'})

@app.get('/api/v1/me/insights')
async def insights(request:Request,user:User):
    with db.connect() as conn:
        counts={row[0]:row[1] for row in conn.execute('SELECT action,count(*) FROM swipes WHERE user_id=? GROUP BY action',(user['id'],))}
        wardrobe_count=conn.execute('SELECT count(*) FROM wardrobe WHERE user_id=?',(user['id'],)).fetchone()[0]
    p=json.loads(user['preferences'])
    strongest=sorted(p.get('learned',{}).items(),key=lambda x:-x[1])[:6]
    return ok(request,{'interactions':counts,'wardrobe_count':wardrobe_count,'strongest_signals':[{'feature':k,'weight':v} for k,v in strongest],'inspirations':p.get('inspirations',[]),'confidence':None})

from fastapi.staticfiles import StaticFiles
from pathlib import Path
ASSETS=Path(__file__).resolve().parents[1]/'runtime/assets'
ASSETS.mkdir(parents=True,exist_ok=True)
app.mount('/assets',StaticFiles(directory=str(ASSETS)),name='reference-assets')

from .schemas import AvatarDesign
@app.post('/api/v1/stylist/avatar')
async def avatar(request:Request,user:User):
    p=personal.context(user)
    prompt=('Design an abstract illustrated fashion mannequin outfit from these clothing preferences. Return four harmonious six-digit hex colours, a silhouette, and a short explanation. '
        'Do not infer appearance, skin, ethnicity, gender or likeness. This is a stylised fashion figure, not a photograph or fit simulation. Preferences: '+json.dumps({k:v for k,v in p.items() if not k.startswith('_')}))
    result=await gemini([{'role':'user','parts':[{'text':prompt}]}],schema=AvatarDesign.model_json_schema())
    try: design=AvatarDesign.model_validate_json(''.join(x.get('text','') for x in result.get('parts',[])))
    except (ValueError,ValidationError):raise ProviderError('INVALID_MODEL_OUTPUT','Avatar design was invalid. Please try again.',502)
    width={'relaxed':75,'tailored':58,'oversized':90}[design.silhouette]
    # Only schema-validated colour strings and a bounded integer enter the SVG. No model SVG/code is executed.
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="440" height="640" viewBox="0 0 440 640"><rect width="440" height="640" fill="{design.backdrop_color}"/><ellipse cx="220" cy="595" rx="95" ry="12" fill="#000000" opacity=".08"/><path d="M181 130Q177 75 220 70Q264 75 259 130L245 173H195Z" fill="#D9D3C7"/><path d="M195 157L195 186H245V157" fill="#D9D3C7"/><path d="M{220-width} 185L195 174Q220 192 245 174L{220+width} 185L{230+width} 340L{208+width} 346L{205+width} 260L{205+width} 375H{235-width}V260L{232-width} 346L{210-width} 340Z" fill="{design.top_color}"/><path d="M{235-width} 370H{205+width}L285 566H231L220 435L208 566H153Z" fill="{design.bottom_color}"/><path d="M153 558H208V586H133Q130 567 153 558M231 558H285L308 578V586H231Z" fill="{design.shoe_color}"/><path d="M180 105Q180 67 220 65Q260 67 261 105L247 89Q221 106 190 94Z" fill="#393A36"/><path d="M220 206V358" stroke="#FFFFFF" stroke-width="1" opacity=".2"/><text x="220" y="625" text-anchor="middle" font-family="Georgia" font-size="9" letter-spacing="4" fill="#333333">ALLURÉ / STYLE STUDY</text></svg>'''
    return ok(request,{'svg':svg,'explanation':design.explanation,'method':'local_or_hosted_llm_design_with_safe_vector_rendering','notice':'AI-styled illustration, not a personal likeness or physical-fit preview.'})
