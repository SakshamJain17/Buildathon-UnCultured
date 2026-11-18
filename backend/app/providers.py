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

async def _generate(contents,*,schema=None,tools=None):
    has_images=any('inlineData' in part for content in contents for part in content.get('parts',[]))
    provider=settings.vision_provider if has_images else settings.llm_provider
    if provider == 'ollama':
        return await ollama_generate(contents,schema=schema,tools=tools)
    if provider != 'gemini':
        raise ProviderError(message='Unsupported model provider; choose ollama or gemini.')
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


async def ollama_generate(contents,*,schema=None,tools=None):
    has_images=any('inlineData' in part for content in contents for part in content.get('parts',[]))
    model=settings.ollama_vision_model if has_images else settings.ollama_model
    if not model:
        raise ProviderError(message='Configure OLLAMA_VISION_MODEL with an installed vision-capable model for photo analysis.')
    messages=[]
    for content in contents:
        parts=content.get('parts',[])
        responses=[p['functionResponse'] for p in parts if 'functionResponse' in p]
        if responses:
            for response in responses:
                messages.append({'role':'tool','tool_name':response['name'],'content':json.dumps(response['response'])})
            continue
        message={'role':'assistant' if content.get('role')=='model' else 'user','content':'\n'.join(p.get('text','') for p in parts)}
        images=[p['inlineData']['data'] for p in parts if 'inlineData' in p]
        if images: message['images']=images
        functions=[p['functionCall'] for p in parts if 'functionCall' in p]
        if functions:
            message['tool_calls']=[{'type':'function','function':{'name':f['name'],'arguments':f.get('args',{})}} for f in functions]
        messages.append(message)
    payload={'model':model,'messages':messages,'stream':False,'think':False,'options':{'temperature':0.2,'num_ctx':8192 if has_images else 16384}}
    if has_images: payload.pop('think',None)
    if schema: payload['format']=schema
    if tools: payload['tools']=[{'type':'function','function':f} for f in tools]
    # Operator-configured URL only, never accepted from API request bodies.
    data=await request_json('POST',settings.ollama_base_url.rstrip('/')+'/api/chat',json=payload,retry=False,timeout=80)
    message=data.get('message',{})
    parts=[]
    if message.get('content'): parts.append({'text':message['content']})
    for item in message.get('tool_calls',[]):
        f=item.get('function',{})
        args=f.get('arguments',{})
        if isinstance(args,str):
            try: args=json.loads(args)
            except ValueError: args={}
        parts.append({'functionCall':{'name':f.get('name'),'args':args}})
    if not parts: raise ProviderError('MODEL_NO_RESULT','Local model returned no usable answer.',502)
    return {'role':'model','parts':parts}


_model_slots=asyncio.Semaphore(2)
async def gemini(contents,*,schema=None,tools=None):
    try: await asyncio.wait_for(_model_slots.acquire(),timeout=3)
    except asyncio.TimeoutError: raise ProviderError('MODEL_BUSY','The demo stylist is helping other visitors. Please retry in a moment.',429)
    try: return await _generate(contents,schema=schema,tools=tools)
    finally: _model_slots.release()
