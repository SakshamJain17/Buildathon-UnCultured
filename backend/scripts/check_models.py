"""List local model capabilities and accessible Gemini model identifiers, never credentials."""
import asyncio,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import settings
from app.providers import request_json,ProviderError

async def run():
    try:
        data=await request_json('GET',settings.ollama_base_url.rstrip('/')+'/api/tags',retry=False,timeout=5)
        print('Installed Ollama models:')
        for model in data.get('models',[]):
            details=await request_json('POST',settings.ollama_base_url.rstrip('/')+'/api/show',json={'model':model['name']},retry=False,timeout=5)
            print(' ',model['name'],'capabilities:',', '.join(details.get('capabilities',[])))
    except ProviderError:
        print('Ollama unavailable. Start ollama serve on the backend machine.')
    if settings.gemini_api_key:
        try:
            data=await request_json('GET','https://generativelanguage.googleapis.com/v1beta/models',headers={'x-goog-api-key':settings.gemini_api_key},retry=False)
            print('Accessible Gemini generateContent models (first page):')
            for m in data.get('models',[]):
                if 'generateContent' in m.get('supportedGenerationMethods',[]): print(' ',m['name'])
        except ProviderError:
            print('Gemini model listing unavailable; verify account access and credential.')

asyncio.run(run())
