import asyncio
import json
import re
import time
from copy import deepcopy
from urllib.parse import urlparse
import httpx
from .config import settings

class ProviderError(Exception):
    def __init__(self,code='PROVIDER_UNAVAILABLE',message='Provider unavailable',status=503):
        self.code,self.message,self.status=code,message,status

async def request_json(method,url,*,retry=True,**kwargs):
    # Do not log URLs or exceptions: query parameters may contain credentials.
    for attempt in range(3 if retry else 1):
        try:
            async with httpx.AsyncClient(timeout=35,follow_redirects=False) as client:
                r=await client.request(method,url,**kwargs)
            if r.status_code==429 or r.status_code>=500:
                if retry and attempt<2:
                    await asyncio.sleep(0.4*2**attempt)
                    continue
                raise ProviderError('PROVIDER_RATE_LIMIT' if r.status_code==429 else 'PROVIDER_UNAVAILABLE','Provider is busy; please retry later.',503)
            if not r.is_success:
                raise ProviderError('PROVIDER_REJECTED','Provider rejected the request. Check credentials, credits, and input compatibility.',502)
            return r.json()
        except (httpx.HTTPError,ValueError):
            if retry and attempt<2:
                await asyncio.sleep(0.4*2**attempt)
                continue
            raise ProviderError(message='Provider request failed or returned invalid data.')
    raise ProviderError()

async def gemini(contents,*,schema=None,tools=None):
    if not settings.gemini_api_key or not settings.gemini_model:
        raise ProviderError(message='Configure GEMINI_API_KEY and GEMINI_MODEL for AI analysis and tool calling.')
    model=settings.gemini_model.removeprefix('models/')
    if not re.fullmatch(r'[A-Za-z0-9._-]+',model):
        raise ProviderError(message='Invalid configured Gemini model identifier.')
    body={'contents':contents,'generationConfig':{'temperature':0.2}}
    if schema:
        body['generationConfig'].update(responseMimeType='application/json',responseJsonSchema=schema)
    if tools:
        body['tools']=[{'functionDeclarations':tools}]
    data=await request_json('POST',f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',headers={'x-goog-api-key':settings.gemini_api_key},json=body)
    try:
        return data['candidates'][0]['content']
    except (KeyError,IndexError,TypeError):
        raise ProviderError('MODEL_NO_RESULT','The model did not return a usable result.',502)

_cache={}
async def cached_get(key,url,params,ttl=600):
    if key in _cache and _cache[key][0]>time.monotonic():
        return deepcopy(_cache[key][1])
    result=await request_json('GET',url,params=params)
    if len(_cache)>256:
        _cache.clear()
    _cache[key]=(time.monotonic()+ttl,deepcopy(result))
    return result

def public_url(value):
    if not isinstance(value,str): return None
    p=urlparse(value)
    return value if p.scheme=='https' and p.hostname and not p.username and not p.password else None
