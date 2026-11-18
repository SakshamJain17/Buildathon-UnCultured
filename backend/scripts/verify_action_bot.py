"""Live local-model rehearsal of the bot's actual persisted mutations."""
import httpx,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
report=[]
with httpx.Client(base_url='http://127.0.0.1:8766',timeout=110) as c:
    token=c.post('/api/v1/sessions',json={'name':'Disposable action rehearsal'}).json()['data']['token']
    c.headers['Authorization']='Bearer '+token
    catalogue=c.get('/api/v1/catalogue').json()['data']['products'];assert catalogue and 'reference_price' not in catalogue[0]
    selected=catalogue[0]['id']
    seed=c.post('/api/v1/demo/seed',json={}).json()['data'];assert seed['sample_wardrobe_items']==6
    repeated=c.post('/api/v1/demo/seed',json={}).json()['data'];assert repeated['seeded'] is False
    def run(message,previous=None):
        body={'message':message,'selected_product_id':selected}
        if previous:body['previous_run_id']=previous
        t=time.monotonic();r=c.post('/api/v1/agent/shop',json=body);assert r.status_code==200,r.text
        data=r.json()['data'];report.append({'message':message,'status':data['status'],'tools':[x['tool'] for x in data['trace']],'ui_actions':data['ui_actions'],'seconds':round(time.monotonic()-t,2)})
        print(json.dumps(report[-1]),flush=True)
        (ROOT/'runtime/action-verification.json').write_text(json.dumps(report,indent=2))
        return data
    first=run('Save this selected piece using record_product_feedback and report my style progress.')
    assert any(x['tool']=='record_product_feedback' and x['status']=='completed' for x in first['trace'])
    saved=c.get('/api/v1/saved').json()['data']['products'];assert selected in [p['id'] for p in saved]
    second=run('Change only my preferred colours to black and white using update_style_preferences.',first['run_id'])
    assert set(c.get('/api/v1/me').json()['data']['preferences']['preferred_colors'])=={'black','white'}
    third=run('Dismiss this selected piece. I never want to see it recommended again.',second['run_id'])
    feed=c.get('/api/v1/recommendations?include_seen=true&limit=50').json()['data']['items'];assert selected not in [x['product']['id'] for x in feed]
    fourth=run('Open my wardrobe screen using open_app_feature.')
    assert any(x.get('feature')=='wardrobe' for x in fourth['ui_actions'])
    c.delete('/api/v1/me')
print('PASS: real model save, preference patch, permanent dismissal and UI navigation verified; disposable session deleted.',flush=True)
