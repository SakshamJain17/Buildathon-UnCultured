"""Fetch only the product photographs explicitly supplied in the frontend brief."""
import asyncio,json,io
from pathlib import Path
import httpx
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'runtime/assets/products';DEST.mkdir(parents=True,exist_ok=True)
items=json.loads((ROOT/'app/data/reference_catalogue.json').read_text())
async def main():
    sem=asyncio.Semaphore(5)
    async with httpx.AsyncClient(timeout=30,headers={'User-Agent':'Mozilla/5.0'},follow_redirects=True) as client:
        async def fetch(p):
            async with sem:
                dest=DEST/(p['id']+'.jpg')
                if dest.exists():return True
                try:
                    r=await client.get(p['image_source']);r.raise_for_status()
                    image=Image.open(io.BytesIO(r.content)).convert('RGB');image.thumbnail((1000,1000));image.save(dest,quality=88)
                    return True
                except Exception:return False
        results=await asyncio.gather(*(fetch(p) for p in items))
        print(f'Fetched {sum(results)}/{len(items)} reference photographs. Prices remain unverified and are not merchant offers.')
asyncio.run(main())
