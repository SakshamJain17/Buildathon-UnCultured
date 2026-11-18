"""Small deterministic fixture evaluation, never evidence of live provider quality."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import intelligence,db

def evaluate():
    t=dict(id='shirt',title='Acme beige shirt',brand='Acme',model_number='123',size='M',colors=['beige'],price=1500,currency='INR',shipping_cost=0,merchant='A')
    cases=[({**t,'id':'same'},'exact_verified_match'),({**t,'id':'size','size':'L'},'similar_alternative'),({**t,'id':'unknown','size':None},'probable_match'),({**t,'id':'brand','brand':'Different','model_number':None},'similar_alternative')]
    predictions=[intelligence.match(t,p)['label'] for p,_ in cases]
    exact_indices=[i for i,p in enumerate(predictions) if p=='exact_verified_match']
    false=sum(cases[i][1]!='exact_verified_match' for i in exact_indices)
    products=db.seed_products(); liked=next(p for p in products if p['id']=='graphic-tee')
    before=[x['product']['id'] for x in intelligence.rank({},products)]
    prefs={}
    for _ in range(5): prefs=intelligence.adapt(prefs,liked,'like')
    after=[x['product']['id'] for x in intelligence.rank(prefs,products)]
    offers=[{**t,'id':'b','price':1200,'shipping_cost':500,'merchant':'B'},t]
    compared=intelligence.compare(t,offers)
    return {'evaluation_scope':'small synthetic fixtures; no live-provider quality measured','matching':{'cases':len(cases),'correct':sum(p==expected for p,(_,expected) in zip(predictions,cases)),'exact_precision':(len(exact_indices)-false)/len(exact_indices) if exact_indices else None,'false_exact_count':false},'recommendations':{'target':'graphic-tee','rank_before':before.index('graphic-tee')+1,'rank_after_five_likes':after.index('graphic-tee')+1,'top5_category_count':len({x['product']['category'] for x in intelligence.rank(prefs,products)[:5]})},'prices':{'shipping_order_correct':compared['lowest_observed']['product']['id']=='shirt'},'live_providers':{'vision':'not tested','shopping':'not tested','tryon':'not tested'}}

if __name__=='__main__':
    result=evaluate(); output=Path(__file__).resolve().parents[1]/'runtime'/'evaluations.json'
    output.parent.mkdir(exist_ok=True); output.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2)); print('Saved:',output)
