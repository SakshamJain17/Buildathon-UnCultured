"""Real HTTP smoke tests against configured providers; records only non-secret outcomes."""
from pathlib import Path
import httpx,json,time
ROOT=Path(__file__).resolve().parents[1]
report={'scope':'single-run live smoke checks, not a quality benchmark','checks':[]}
with httpx.Client(base_url='http://127.0.0.1:8766',timeout=150) as c:
    session=c.post('/api/v1/sessions',json={'name':'Live integration test'}).json()['data']
    c.headers['Authorization']='Bearer '+session['token']
    def check(name,method,path,**kwargs):
        t=time.monotonic();r=c.request(method,path,**kwargs)
        try:body=r.json()
        except ValueError:body={}
        data=body.get('data',{})
        item={'name':name,'http_status':r.status_code,'seconds':round(time.monotonic()-t,2)}
        if r.status_code>=400:item['error']=body.get('error')
        if name=='agent':item['run_status']=data.get('status');item['tools']=[x['tool'] for x in data.get('trace',[])]
        if name=='avatar':item['valid_svg']=data.get('svg','').startswith('<svg')
        if name=='vision':item['source_image_count']=data.get('source_image_count');item['aesthetics']=data.get('style_profile',{}).get('aesthetics')
        report['checks'].append(item);print(json.dumps(item),flush=True)
        (ROOT/'runtime/live-integration-results.json').write_text(json.dumps(report,indent=2))
        return data
    check('preferences','PUT','/api/v1/me/preferences',json={'aesthetics':['minimalist'],'preferred_colors':['beige','olive'],'silhouettes':['relaxed']})
    feed=check('recommendations','GET','/api/v1/recommendations?limit=50')
    first=feed['items'][0]['product'];check('swipe','POST','/api/v1/swipes',json={'product_id':first['id'],'action':'dislike'})
    new=check('dismissed_feed','GET','/api/v1/recommendations?include_seen=true&limit=50')
    assert first['id'] not in [x['product']['id'] for x in new['items']]
    check('weather','POST','/api/v1/stylist/daily',json={'location':{'latitude':28.46,'longitude':77.03}})
    files=sorted((ROOT/'runtime/assets/products').glob('*.jpg'))[:5]
    wardrobe=check('wardrobe','POST','/api/v1/wardrobe',files={'image':('garment.jpg',files[0].read_bytes(),'image/jpeg')},data={'title':'Test garment','category':'tops','color':'beige'})
    check('wardrobe_outfit','POST','/api/v1/wardrobe/outfits')
    check('inspiration','PUT','/api/v1/me/inspirations',json={'inspirations':[{'name':'Test inspiration','tags':['minimalist']}]})
    check('palette','POST','/api/v1/style/palette',json={'undertone':'neutral','consent':True})
    check('hair','POST','/api/v1/stylist/hair',json={'length':'short','texture':'wavy','goal':'Three concise low-maintenance ideas.'})
    check('avatar','POST','/api/v1/stylist/avatar',json={})
    run=check('agent','POST','/api/v1/agent/shop',json={'message':'Use retrieve_style_profile and search_demo_catalogue to find two minimalist shirts. Label references and do not invent prices.'})
    if run.get('status')=='completed':check('follow_up','POST','/api/v1/agent/shop',json={'message':'Which of those works best for relaxed styling? Keep it concise.','previous_run_id':run['run_id']})
    check('vision','POST','/api/v1/style/analyze',files=[('images',(f.name,f.read_bytes(),'image/jpeg')) for f in files])
    check('shopping_missing_key','POST','/api/v1/products/search',json={'query':'beige shirt'})
    check('tryon_missing_key','POST','/api/v1/tryon',files={'person_image':('reference.jpg',files[0].read_bytes(),'image/jpeg'),'garment_image':('garment.jpg',files[1].read_bytes(),'image/jpeg')},data={'consent':'true'})
    check('cleanup_disposable_session','DELETE','/api/v1/me')
print('Saved runtime/live-integration-results.json',flush=True)
