import hashlib
import json
import math
import re
from difflib import SequenceMatcher
from . import db
from .providers import cached_get,ProviderError,public_url
from .config import settings
from .schemas import SearchIn

async def weather(latitude,longitude):
    # Rounded only in transit/cache; exact coordinates are never persisted.
    lat,lon=round(latitude,2),round(longitude,2)
    result=await cached_get(('weather',lat,lon),'https://api.open-meteo.com/v1/forecast',{
        'latitude':lat,'longitude':lon,'current':'temperature_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m',
        'daily':'temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum',
        'timezone':'auto','forecast_days':1},ttl=600)
    try:
        current=result['current']; daily=result['daily']
        probability=daily['precipitation_probability_max'][0]
        precipitation=current.get('precipitation') or 0
        temperature=current['apparent_temperature']
        if temperature is None: raise ValueError()
        tags=['hot' if temperature>=30 else 'warm' if temperature>=24 else 'cold' if temperature<16 else 'mild']
        if precipitation>0 or (probability is not None and probability>=50): tags.append('rain')
        return {'current':current,'daily':{k:v[0] for k,v in daily.items()},'tags':tags,'timezone':result['timezone'],
            'source':'Open-Meteo','source_url':'https://open-meteo.com/','retrieved_at':db.now(),
            'precipitation_probability_percent':probability,'currently_precipitating':precipitation>0}
    except (KeyError,IndexError,TypeError,ValueError):
        raise ProviderError('WEATHER_UNAVAILABLE','Forecast is incomplete; weather advice is unavailable.')

async def cities(query):
    data=await cached_get(('city',query.lower()),'https://geocoding-api.open-meteo.com/v1/search',{'name':query,'count':5,'language':'en','format':'json'},ttl=3600)
    return [{'name':r['name'],'region':r.get('admin1'),'country':r.get('country'),'latitude':r['latitude'],'longitude':r['longitude'],'timezone':r.get('timezone')} for r in data.get('results',[])]

def features(p):
    result=[]
    for key in ('colors','aesthetics','fits'):
        result += [f'{key}:{str(v).lower()}' for v in p.get(key,[])]
    if p.get('category'): result.append('category:'+p['category'].lower())
    return result

def rank(preferences,items,weather_tags=(),budget=None,excluded=()):
    desired={}
    for key,source in [('colors','preferred_colors'),('aesthetics','aesthetics'),('fits','silhouettes'),('category','garment_preferences')]:
        for value in preferences.get(source,[]): desired[f'{key}:{value.lower()}']=1.0
    learned=preferences.get('learned',{})
    output=[]
    for p in items:
        if p['id'] in excluded: continue
        ceiling=budget or preferences.get('budget')
        if ceiling and (p.get('price') is None or p['price']>ceiling): continue
        score=0.0; reasons=[]
        for f in features(p):
            if f in desired:
                score+=desired[f]; reasons.append('Matches your '+f.split(':',1)[1]+' preference')
            score+=max(-0.75,min(0.75,learned.get(f,0)))
        for tag in weather_tags:
            if tag in p.get('weather_tags',[]):
                score+=1.2; reasons.append('Suitable for '+tag+' conditions in this catalogue')
        if 'rain' in weather_tags and 'water_resistant' in p.get('functional_tags',[]):
            score+=2; reasons.append('Listed as water-resistant')
        output.append({'product':p,'score':round(score,4),'reasons':reasons or ['An exploratory option outside your current favourites']})
    output.sort(key=lambda x:(-x['score'],x['product']['id']))
    # Greedy category diversity; retain raw scores for explainability.
    chosen=[]; counts={}
    while output:
        best=max(range(len(output)),key=lambda i:output[i]['score']-0.6*counts.get(output[i]['product'].get('category'),0))
        entry=output.pop(best); chosen.append(entry)
        category=entry['product'].get('category'); counts[category]=counts.get(category,0)+1
    return chosen

def adapt(preferences,product,action):
    result=dict(preferences); learned=dict(result.get('learned',{}))
    coefficient={'like':0.16,'dislike':-0.16,'save':0.08}[action]
    for f in features(product): learned[f]=round(max(-0.75,min(0.75,learned.get(f,0)*0.98+coefficient)),4)
    result['learned']=learned
    return result

def daily_style(name,preferences,forecast,occasion='everyday'):
    ranking=rank(preferences,db.products(),forecast['tags'])
    outfit=[]
    for category in ('tops','bottoms','footwear'):
        candidate=next((x for x in ranking if x['product'].get('category')==category),None)
        if candidate: outfit.append(candidate)
    probability=forecast['precipitation_probability_percent']
    if forecast['currently_precipitating']:
        opening='precipitation is being reported near you right now'
    elif 'rain' in forecast['tags']:
        opening=f'the forecast gives a {probability}% chance of precipitation today'
    else:
        opening=f"it feels like {forecast['current']['apparent_temperature']}°C near you"
    suggestions=[]
    if 'rain' in forecast['tags']: suggestions+=['Choose a water-resistant outer layer and footwear with grip.','Carry an umbrella; avoid suede if you expect to be outside.']
    if 'hot' in forecast['tags']: suggestions+=['Choose breathable, lightweight layers.']
    if 'cold' in forecast['tags']: suggestions+=['Add an insulating layer you can remove indoors.']
    if not suggestions: suggestions=['Try a comfortable layer you can adjust through the day.']
    return {'greeting':f'Hey {name}, {opening}. '+suggestions[0]+" Make it your own—you’ll look fab.",
        'weather':forecast,'occasion':occasion,'styling_notes':suggestions,'outfit':outfit,
        'mode':'rules_based','warnings':['Demo catalogue items are fictional examples, not purchasable listings.'] if any(x['product'].get('is_demo') for x in outfit) else [],
        'occasion_applied':False,'location_stored':False}

async def search(body:SearchIn):
    if not settings.serpapi_api_key:
        raise ProviderError(message='Configure SERPAPI_API_KEY for real shopping listings.')
    data=await cached_get(('shopping',body.query),'https://serpapi.com/search.json',{
        'engine':'google_shopping','q':body.query,'gl':'in','hl':'en','api_key':settings.serpapi_api_key},ttl=300)
    if data.get('error'): raise ProviderError(message='Shopping provider could not fulfil this search.')
    items=[]
    for r in data.get('shopping_results',[]):
        price=r.get('extracted_price')
        if not isinstance(price,(int,float)) or not math.isfinite(price) or price<0: price=None
        # Only label INR when the observed text explicitly establishes it.
        price_text=str(r.get('price',''))
        currency='INR' if '₹' in price_text or re.search(r'\b(?:INR|Rs\.?)[\s\d]',price_text) else 'UNKNOWN'
        if body.max_price and (price is None or currency!='INR' or price>body.max_price): continue
        url=public_url(r.get('product_link')) or public_url(r.get('link'))
        if not url: continue
        title=str(r.get('title','')).strip()
        if not title: continue
        p={'id':'live_'+hashlib.sha256((str(r.get('product_id',''))+url+str(r.get('source',''))).encode()).hexdigest()[:24],
            'title':title[:500],'brand':None,'category':None,'colors':[],'aesthetics':[],'fits':[],'weather_tags':[],'functional_tags':[],
            'price':price,'currency':currency,'size':None,'model_number':None,'gtin':None,'shipping_cost':None,
            'image_url':public_url(r.get('thumbnail')),'merchant_url':url,'merchant':r.get('source'),
            'source':'serpapi_google_shopping','is_demo':False,'observed_at':db.now()}
        items.append(p)
        if len(items)>=body.limit: break
    db.save_products(items)
    return {'products':items,'warnings':['Sizes, stock, materials, and shipping are unverified unless explicitly supplied.'],'source':'serpapi_google_shopping','observed_at':db.now()}

def norm(v): return re.sub(r'[^a-z0-9]','',str(v or '').lower())

def match(target,candidate):
    evidence=[]; missing=[]; conflict=[]
    for key in ('brand','model_number','gtin','size'):
        a,b=target.get(key),candidate.get(key)
        if a and b:
            if norm(a)==norm(b): evidence.append(key)
            else: conflict.append(key)
        else: missing.append(key)
    color_a={norm(x) for x in target.get('colors',[])}; color_b={norm(x) for x in candidate.get('colors',[])}
    if color_a and color_b:
        if color_a==color_b: evidence.append('color')
        else: conflict.append('color')
    else: missing.append('color')
    identifier='gtin' in evidence or ('brand' in evidence and 'model_number' in evidence)
    similarity=SequenceMatcher(None,norm(target['title']),norm(candidate['title'])).ratio()
    if identifier and not conflict and 'size' in evidence and 'color' in evidence:
        label='exact_verified_match'
    elif identifier and not conflict:
        label='probable_match'
    elif (target.get('category') and target.get('category')==candidate.get('category')) or similarity>=0.45:
        label='similar_alternative'
    else: label='unrelated'
    return {'product':candidate,'label':label,'matching_evidence':evidence,'conflicts':conflict,'missing_information':missing,
        'verification_scope':'Supplied attributes only; merchant authenticity has not been independently verified.'}

def compare(target,candidates):
    matched=[match(target,p) for p in candidates]
    comparable=[m for m in matched if m['label']=='exact_verified_match' and not m['product'].get('is_demo') and m['product'].get('price') is not None and m['product'].get('currency')==target.get('currency') and target.get('currency')!='UNKNOWN']
    shipping_known=bool(comparable) and all(x['product'].get('shipping_cost') is not None for x in comparable)
    comparable.sort(key=lambda x:x['product']['price']+(x['product']['shipping_cost'] if shipping_known else 0))
    return {'target':target,'matches':matched,'comparable_offers':comparable,'lowest_observed':comparable[0] if comparable else None,
        'price_basis':'price_plus_shipping' if shipping_known else 'listed_price_excluding_unknown_shipping',
        'merchant_count':len({x['product'].get('merchant') for x in comparable}),
        'warnings':(['Shipping is missing; delivered totals cannot be established.'] if not shipping_known else [])+(['No verified comparable offers available.'] if not comparable else []),
        'observed_at':db.now()}

def complete(preferences,target,budget=None):
    remaining=None
    if budget is not None:
        if target.get('price') is None or target.get('currency')!='INR':
            return {'items':[],'known_total':None,'warnings':['The selected item has no verified INR price; a total budget cannot be enforced.']}
        remaining=budget-target['price']
        if remaining<=0: return {'items':[],'known_total':target['price'],'warnings':['The selected item uses the entire budget.']}
    ranked=rank(preferences,[p for p in db.products() if p['id']!=target['id'] and p.get('category')!=target.get('category') and (budget is None or p.get('currency')=='INR')],budget=remaining)
    selected=[]; categories=set(); spent=0
    for item in ranked:
        p=item['product']; price=p.get('price')
        if p.get('category') in categories: continue
        if remaining is not None and (price is None or spent+price>remaining): continue
        selected.append(item); categories.add(p.get('category')); spent+=price or 0
        if len(selected)==2: break
    all_known=target.get('price') is not None and all(x['product'].get('price') is not None and x['product'].get('currency')==target.get('currency') for x in selected)
    return {'items':selected,'known_total':target['price']+spent if all_known else None,'warnings':['Compatibility currently uses preferences and category diversity; occasion and colour-pair scoring are not implemented.']}

def palette(undertone,preference):
    options={
        'warm':[('olive','#6B7044'),('terracotta','#B85C38'),('cream','#F0E6CE'),('camel','#B98B61'),('teal','#207C7A')],
        'cool':[('navy','#243B61'),('berry','#993C68'),('slate','#62758B'),('icy blue','#C2DCEB'),('emerald','#227A60')],
        'neutral':[('navy','#243B61'),('ivory','#F1EDE3'),('forest','#365C46'),('rose','#BC7D84'),('charcoal','#3B3E42')],
        'unsure':[('navy','#243B61'),('cream','#F0E6CE'),('olive','#6B7044'),('berry','#993C68'),('teal','#207C7A')],
    }
    return {'selected_undertone':undertone,'preference':preference,'colors':[{'name':n,'hex':h} for n,h in options[undertone]],
        'explanation':'A starting palette to explore based on the undertone you selected. Try colours you enjoy; none are forbidden.',
        'method':'curated_style_heuristic','confidence':None,'stored':False,
        'warnings':['This is subjective styling guidance, not a measurement of your complexion.','The intensity preference is recorded in this response but does not yet alter the palette.']}
