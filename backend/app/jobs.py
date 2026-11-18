import asyncio
import base64
import json
from . import db
from .config import settings
from .providers import request_json,ProviderError

async def run_tryon(job_id,person,garment,category):
    data={'category':category,'provider':'fashn','provider_job_id':None,'generated_image_url':None,'error':None}
    try:
        db.update_job(job_id,'processing',data)
        # Paid submissions are never retried automatically: upstream idempotency is not guaranteed.
        result=await request_json('POST','https://api.fashn.ai/v1/run',retry=False,
            headers={'Authorization':'Bearer '+settings.fashn_api_key},
            json={'model_name':'tryon-v1.6','inputs':{'model_image':person,'garment_image':garment,'category':category,'num_samples':1,'moderation_level':'conservative'}})
        provider_id=result.get('id')
        if not provider_id:
            raise ProviderError('TRYON_REJECTED','Try-on provider did not return a prediction ID.',502)
        data['provider_job_id']=provider_id
        db.update_job(job_id,'processing',data)
    except ProviderError as exc:
        data['error']={'code':exc.code,'message':exc.message}
        db.update_job(job_id,'failed',data)
    except Exception:
        data['error']={'code':'TRYON_FAILED','message':'Generation could not be submitted.'}
        db.update_job(job_id,'failed',data)
    # Never persist input photographs. A restart during submission is explicitly marked failed.

async def refresh_tryon(row):
    data=json.loads(row['data'])
    if row['status']!='processing' or not data.get('provider_job_id'): return row
    from urllib.parse import quote
    result=await request_json('GET','https://api.fashn.ai/v1/status/'+quote(data['provider_job_id'],safe=''),headers={'Authorization':'Bearer '+settings.fashn_api_key})
    status=result.get('status')
    if status=='completed':
        outputs=result.get('output',[])
        from .providers import public_url
        url=public_url(outputs[0]) if outputs else None
        if url:
            data['generated_image_url']=url; db.update_job(row['id'],'completed',data)
        else:
            data['error']={'code':'INVALID_OUTPUT','message':'Provider returned no usable image URL.'}; db.update_job(row['id'],'failed',data)
    elif status in {'failed','canceled','cancelled'}:
        data['error']={'code':'GENERATION_FAILED','message':'Provider could not generate this combination. Try a clear, front-facing photograph.'}
        db.update_job(row['id'],'failed',data)
    return db.get_job(row['id'],row['user_id'])
