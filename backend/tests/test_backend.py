import io,json
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app import db,intelligence,main,agent,jobs
from app.config import settings

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(settings,'database_path',str(tmp_path/'test.sqlite3'))
    monkeypatch.setattr(settings,'llm_provider','gemini')
    monkeypatch.setattr(settings,'vision_provider','gemini')
    for key in ('gemini_api_key','gemini_model','fashn_api_key','serpapi_api_key'): monkeypatch.setattr(settings,key,'')
    with TestClient(main.app) as c: yield c

@pytest.fixture
def auth(client):
    data=client.post('/api/v1/sessions',json={'name':'Saksham'}).json()['data']
    return {'Authorization':'Bearer '+data['token']}

def image():
    out=io.BytesIO(); Image.new('RGB',(256,256),'beige').save(out,format='PNG'); return out.getvalue()

def uploads(n=5): return [('images',('reference.png',image(),'image/png')) for _ in range(n)]

def test_sessions_and_input_validation(client,auth):
    assert client.get('/api/v1/health').status_code==200
    assert client.get('/api/v1/me').status_code==401
    first=client.get('/api/v1/me',headers=auth).json()['data']
    other=client.post('/api/v1/sessions',json={'name':'Other'}).json()['data']
    assert client.get('/api/v1/users/'+first['user_id']+'/preferences',headers={'Authorization':'Bearer '+other['token']}).status_code==404
    assert client.put('/api/v1/me/preferences',headers=auth,json={'budget':-1}).status_code==422
    assert client.post('/api/v1/stylist/daily',headers=auth,json={'location':{'latitude':999,'longitude':77}}).status_code==422

def test_swipes_persistence_and_idempotency(client,auth):
    client.put('/api/v1/me/preferences',headers=auth,json={'aesthetics':['minimalist']})
    for _ in range(4):
        assert client.post('/api/v1/swipes',headers=auth,json={'product_id':'graphic-tee','action':'like'}).status_code==200
    before=client.get('/api/v1/me',headers=auth).json()['data']['preferences']['learned']['colors:red']
    for _ in range(2): client.post('/api/v1/swipes',headers={**auth,'Idempotency-Key':'once'},json={'product_id':'graphic-tee','action':'dislike'})
    after=client.get('/api/v1/me',headers=auth).json()['data']['preferences']['learned']['colors:red']
    assert after==round(before*.98-.16,4)
    items=client.get('/api/v1/recommendations',headers=auth).json()['data']['items']
    assert 'graphic-tee' not in [x['product']['id'] for x in items]
    client.post('/api/v1/swipes',headers=auth,json={'product_id':'neutral-shirt','action':'save'})
    assert client.get('/api/v1/saved',headers=auth).json()['data']['products'][0]['id']=='neutral-shirt'

def test_learning_changes_rank():
    products=db.seed_products(); target=next(p for p in products if p['id']=='graphic-tee'); prefs={}
    before=[x['product']['id'] for x in intelligence.rank(prefs,products)]
    for _ in range(5): prefs=intelligence.adapt(prefs,target,'like')
    positive=[x['product']['id'] for x in intelligence.rank(prefs,products)]
    assert positive.index('graphic-tee')<before.index('graphic-tee')
    for _ in range(12): prefs=intelligence.adapt(prefs,target,'dislike')
    negative=[x['product']['id'] for x in intelligence.rank(prefs,products)]
    assert negative.index('graphic-tee')>positive.index('graphic-tee')
    assert all(abs(v)<=.75 for v in prefs['learned'].values())

def test_upload_validation(client,auth):
    assert client.post('/api/v1/style/analyze',headers=auth,files=uploads(4)).status_code==422
    assert client.post('/api/v1/style/analyze',headers=auth,files=[('images',('fake.png',b'bad','image/png'))]*5).status_code==422
    assert client.post('/api/v1/style/analyze',headers=auth,files=uploads()).status_code==503

def test_vision_aggregation(client,auth,monkeypatch):
    async def model(*a,**kw):
        item={'aesthetics':['minimalist'],'preferred_colors':['beige'],'silhouettes':['relaxed'],'garment_preferences':['tops'],'visible_materials':['possibly linen'],'uncertainty':['unknown composition']}
        return {'parts':[{'text':json.dumps({'images':[item]*5})}]}
    monkeypatch.setattr(main,'gemini',model)
    result=client.post('/api/v1/style/analyze',headers=auth,files=uploads())
    assert result.status_code==200,result.text
    assert result.json()['data']['style_profile']['preferred_colors']==['beige']
    assert result.json()['data']['confidence'] is None
    assert client.get('/api/v1/me',headers=auth).json()['data']['preferences']['aesthetics']==['minimalist']

def test_bad_vision_output(client,auth,monkeypatch):
    async def bad(*a,**kw): return {'parts':[{'text':'{}'}]}
    monkeypatch.setattr(main,'gemini',bad)
    assert client.post('/api/v1/style/analyze',headers=auth,files=uploads()).status_code==502

def test_rain_personalisation(client,auth,monkeypatch):
    async def forecast(*a): return {'current':{'apparent_temperature':21},'daily':{},'tags':['mild','rain'],'source':'test_fixture','precipitation_probability_percent':80,'currently_precipitating':False}
    monkeypatch.setattr(intelligence,'weather',forecast)
    result=client.post('/api/v1/stylist/daily',headers=auth,json={'location':{'latitude':28.45,'longitude':77.03}})
    assert result.status_code==200,result.text
    data=result.json()['data']; assert 'Hey Saksham' in data['greeting'] and '80%' in data['greeting']
    assert data['outfit'][0]['product']['id']=='rain-shell'
    assert any(x['product']['id']=='rain-boots' for x in data['outfit'])
    assert data['location_stored'] is False

@pytest.mark.asyncio
async def test_forecast_normalisation(monkeypatch):
    async def get(*a,**kw): return {'current':{'apparent_temperature':34,'precipitation':0},'daily':{'precipitation_probability_max':[10]},'timezone':'Asia/Kolkata'}
    monkeypatch.setattr(intelligence,'cached_get',get)
    assert (await intelligence.weather(28.45678,77.0333))['tags']==['hot']

def target(): return dict(id='a',title='Brand X beige shirt',brand='X',model_number='123',size='M',colors=['beige'],price=1500,currency='INR',shipping_cost=None,merchant='Store A',is_demo=False)

def test_identity_and_prices():
    a=target(); b={**a,'id':'b','price':1200,'merchant':'Store B'}
    assert intelligence.match(a,b)['label']=='exact_verified_match'
    assert intelligence.match(a,{**b,'size':'L'})['label']!='exact_verified_match'
    assert intelligence.match(a,{**b,'size':None})['label']=='probable_match'
    assert intelligence.match(a,{**b,'brand':'Other','model_number':None})['label']=='similar_alternative'
    result=intelligence.compare(a,[b,{**b,'id':'usd','price':2,'currency':'USD'}])
    assert result['lowest_observed']['product']['id']=='b'
    assert result['price_basis']=='listed_price_excluding_unknown_shipping'
    a['shipping_cost']=0; b['shipping_cost']=500
    assert intelligence.compare(a,[a,b])['lowest_observed']['product']['id']=='a'

@pytest.mark.asyncio
async def test_search_normalisation(client,monkeypatch):
    monkeypatch.setattr(settings,'serpapi_api_key','test')
    async def get(*a,**kw): return {'shopping_results':[
        {'title':'Shirt','price':'₹1,299','extracted_price':1299,'product_link':'https://example.com/1'},
        {'title':'Costly','price':'₹5,000','extracted_price':5000,'product_link':'https://example.com/2'},
        {'title':'USD','price':'$10','extracted_price':10,'product_link':'https://example.com/3'}]}
    monkeypatch.setattr(intelligence,'cached_get',get)
    result=await intelligence.search(main.SearchIn(query='shirt',max_price=2000))
    assert len(result['products'])==1 and result['products'][0]['brand'] is None


def test_provider_unavailable(client,auth):
    assert client.post('/api/v1/products/search',headers=auth,json={'query':'shirt'}).status_code==503
    data=client.post('/api/v1/agent/shop',headers=auth,json={'message':'Find shirt'}).json()['data']
    assert data['status']=='unavailable' and data['trace']==[]
    assert client.get('/api/v1/agent/runs/'+data['run_id'],headers=auth).status_code==200

def test_tryon_lifecycle(client,auth,monkeypatch):
    monkeypatch.setattr(settings,'fashn_api_key','test')
    async def submit(job_id,*a): db.update_job(job_id,'processing',{'provider_job_id':'p1'})
    monkeypatch.setattr(main,'run_tryon',submit)
    files={k:(k+'.png',image(),'image/png') for k in ('person_image','garment_image')}
    headers={**auth,'Idempotency-Key':'generation-1'}
    result=client.post('/api/v1/tryon',headers=headers,files=files,data={'consent':'true'})
    assert result.status_code==202,result.text
    job=result.json()['data']['job_id']
    assert client.post('/api/v1/tryon',headers=headers,files=files,data={'consent':'true'}).json()['data']['job_id']==job
    async def refresh(row):
        db.update_job(row['id'],'completed',{'generated_image_url':'https://example.com/result.jpg','provider_job_id':'p1'})
        return db.get_job(row['id'],row['user_id'])
    monkeypatch.setattr(main,'refresh_tryon',refresh)
    data=client.get('/api/v1/tryon/'+job,headers=auth).json()['data']
    assert data['status']=='completed' and 'provider_job_id' not in data
    other=client.post('/api/v1/sessions',json={'name':'Other'}).json()['data']
    assert client.get('/api/v1/tryon/'+job,headers={'Authorization':'Bearer '+other['token']}).status_code==404
    assert client.post('/api/v1/tryon',headers=auth,files=files,data={'consent':'false'}).status_code==422

@pytest.mark.asyncio
async def test_fashn_adapter(client,monkeypatch):
    with db.connect() as c:
        c.execute('INSERT INTO users VALUES (?,?,?,?,?)',('u','hash','Name','{}',db.now()))
        c.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?)',('j','u','tryon','queued','{}',db.now(),db.now()))
    async def request(method,url,**kw):
        if method=='POST':
            assert kw['retry'] is False and kw['json']['model_name']=='tryon-v1.6'
            assert 'model_image' in kw['json']['inputs']
            return {'id':'p1'}
        return {'status':'completed','output':['https://example.com/result.jpg']}
    monkeypatch.setattr(jobs,'request_json',request)
    await jobs.run_tryon('j','person','garment','tops')
    assert (await jobs.refresh_tryon(db.get_job('j','u')))['status']=='completed'

def test_agent_tool_loop(client,auth,monkeypatch):
    replies=iter([
        {'role':'model','parts':[{'functionCall':{'name':'retrieve_style_profile','args':{}}}]},
        {'role':'model','parts':[{'functionCall':{'name':'search_products','args':{'query':'beige shirt'}}}]},
        {'role':'model','parts':[{'text':'Shopping unavailable.'}]}])
    async def model(*a,**kw): return next(replies)
    monkeypatch.setattr(agent,'gemini',model)
    data=client.post('/api/v1/agent/shop',headers=auth,json={'message':'Find a beige shirt'}).json()['data']
    assert [x['tool'] for x in data['trace']]==['retrieve_style_profile','search_products']
    assert data['trace'][1]['status']=='failed'

def test_agent_limit(client,auth,monkeypatch):
    async def model(*a,**kw): return {'role':'model','parts':[{'functionCall':{'name':'retrieve_style_profile','args':{}}}]}
    monkeypatch.setattr(agent,'gemini',model)
    data=client.post('/api/v1/agent/shop',headers=auth,json={'message':'Find something'}).json()['data']
    assert data['status']=='limited' and len(data['trace'])==8

def test_cors_deletion(client,auth):
    headers={'Origin':'http://localhost:3000','Access-Control-Request-Method':'GET'}
    assert client.options('/api/v1/me',headers=headers).headers['access-control-allow-origin']==headers['Origin']
    headers['Origin']='https://untrusted.example'
    assert 'access-control-allow-origin' not in client.options('/api/v1/me',headers=headers).headers
    assert client.delete('/api/v1/me',headers=auth).status_code==200
    assert client.get('/api/v1/me',headers=auth).status_code==401

def test_unknown_prices_do_not_pass_budget():
    assert intelligence.rank({},db.seed_products(),budget=2000)==[]
    result=intelligence.complete({},db.seed_products()[0],3000)
    assert result['items']==[] and result['known_total'] is None

def test_optional_palette(client,auth):
    assert client.post('/api/v1/style/palette',headers=auth,json={'undertone':'warm','consent':False}).status_code==422
    data=client.post('/api/v1/style/palette',headers=auth,json={'undertone':'cool','consent':True}).json()['data']
    assert data['method']=='curated_style_heuristic' and data['stored'] is False
    assert data['colors'][0]['name']=='navy'
    assert 'undertone' not in client.get('/api/v1/me',headers=auth).json()['data']['preferences']

@pytest.mark.asyncio
async def test_ollama_translation(client,monkeypatch):
    from app import providers
    monkeypatch.setattr(settings,'llm_provider','ollama')
    monkeypatch.setattr(settings,'ollama_model','local-test')
    async def request(method,url,**kw):
        body=kw['json']
        assert body['model']=='local-test' and body['stream'] is False
        assert body['messages'][1]['role']=='assistant'
        assert body['messages'][2]['role']=='tool'
        return {'message':{'content':'Done','tool_calls':[{'function':{'name':'retrieve_style_profile','arguments':{}}}]}}
    monkeypatch.setattr(providers,'request_json',request)
    result=await providers.gemini([
        {'role':'user','parts':[{'text':'hello'}]},
        {'role':'model','parts':[{'functionCall':{'name':'retrieve_style_profile','args':{}}}]},
        {'role':'user','parts':[{'functionResponse':{'name':'retrieve_style_profile','response':{'preferences':{}}}}]},
    ],tools=agent.TOOLS)
    assert result['parts'][1]['functionCall']['name']=='retrieve_style_profile'

@pytest.mark.asyncio
async def test_ollama_requires_vision_model(client,monkeypatch):
    monkeypatch.setattr(settings,'vision_provider','ollama')
    from app import providers
    monkeypatch.setattr(settings,'llm_provider','ollama')
    monkeypatch.setattr(settings,'ollama_vision_model','')
    with pytest.raises(providers.ProviderError):
        await providers.gemini([{'role':'user','parts':[{'inlineData':{'data':'test'}}]}])

def test_dismissal_survives_duplicate_ids_and_daily(client,auth,monkeypatch):
    client.post('/api/v1/swipes',headers=auth,json={'product_id':'rain-shell','action':'dislike'})
    original=next(x for x in db.products() if x['id']=='rain-shell')
    duplicate={**original,'id':'different-merchant-id'};db.save_products([duplicate])
    items=client.get('/api/v1/recommendations?include_seen=true',headers=auth).json()['data']['items']
    assert not {'rain-shell','different-merchant-id'} & {x['product']['id'] for x in items}
    async def forecast(*a):return {'current':{'apparent_temperature':21},'daily':{},'tags':['mild','rain'],'source':'fixture','precipitation_probability_percent':80,'currently_precipitating':False}
    monkeypatch.setattr(intelligence,'weather',forecast)
    result=client.post('/api/v1/stylist/daily',headers=auth,json={'location':{'latitude':28,'longitude':77}}).json()['data']
    assert not {'rain-shell','different-merchant-id'} & {x['product']['id'] for x in result['outfit']}
    other=client.post('/api/v1/sessions',json={'name':'Other'}).json()['data']
    other_items=client.get('/api/v1/recommendations?limit=50',headers={'Authorization':'Bearer '+other['token']}).json()['data']['items']
    assert 'rain-shell' in {x['product']['id'] for x in other_items}

def test_private_wardrobe(client,auth):
    result=client.post('/api/v1/wardrobe',headers=auth,files={'image':('shirt.png',image(),'image/png')},data={'title':'My shirt','category':'tops','color':'olive'})
    assert result.status_code==201,result.text
    item=result.json()['data']['item'];item_id=item['id']
    assert client.get('/api/v1/wardrobe/'+item_id+'/image',headers=auth).headers['content-type']=='image/jpeg'
    assert client.get('/api/v1/wardrobe',headers=auth).json()['data']['items'][0]['id']==item_id
    assert client.post('/api/v1/wardrobe/outfits',headers=auth).json()['data']['items'][0]['product']['id']==item_id
    other=client.post('/api/v1/sessions',json={'name':'Other'}).json()['data']
    other_auth={'Authorization':'Bearer '+other['token']}
    assert client.get('/api/v1/wardrobe/'+item_id+'/image',headers=other_auth).status_code==404
    assert client.delete('/api/v1/wardrobe/'+item_id,headers=other_auth).status_code==404
    assert client.delete('/api/v1/wardrobe/'+item_id,headers=auth).status_code==200

def test_inspiration_and_hair(client,auth,monkeypatch):
    assert client.put('/api/v1/me/inspirations',headers=auth,json={'inspirations':[{'name':'A creator','tags':['streetwear']}]}).status_code==200
    assert client.get('/api/v1/me',headers=auth).json()['data']['preferences']['inspirations'][0]['name']=='A creator'
    async def model(*a,**kw):return {'parts':[{'text':'Try three low-maintenance styles.'}]}
    monkeypatch.setattr(main,'gemini',model)
    result=client.post('/api/v1/stylist/hair',headers=auth,json={'length':'short','texture':'wavy','goal':'Low maintenance'})
    assert result.status_code==200 and result.json()['data']['photo_analysis'] is False
