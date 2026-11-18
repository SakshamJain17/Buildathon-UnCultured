"""Package ALLURE's public frontend for Vercel. Never copies provider keys or user data."""
import argparse,hashlib,json,re,shutil
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
repo=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=repo/'web/.screenshots/vercel-allure');parser.add_argument('--backend',default='https://fioricet-handheld-gamma-mechanics.trycloudflare.com');args=parser.parse_args()
origin=args.backend.rstrip('/')
u=urlparse(origin)
if u.scheme!='https' or not u.netloc or u.path or u.username:raise SystemExit('Use the public HTTPS backend origin, without a path.')
root=args.output;root.mkdir(parents=True,exist_ok=True);(root/'assets/products').mkdir(parents=True,exist_ok=True)
public=[]
for p in json.loads((repo/'backend/app/data/reference_catalogue.json').read_text()):
 source=repo/'backend/runtime'/p['image_url'].lstrip('/')
 if not source.is_file():continue
 target=root/p['image_url'].lstrip('/');im=Image.open(source).convert('RGB');im.thumbnail((640,800));im.save(target,quality=80,optimize=True)
 public.append({k:p[k] for k in ('id','title','category','image_url')})
(root/'catalogue.json').write_text(json.dumps({'data':{'products':public}},ensure_ascii=False))
for source,target in [('story.html','index.html'),('film.html','film.html')]:
 (root/target).write_text((repo/'web'/source).read_text().replace("fetch('/api/v1/catalogue')","fetch('/catalogue.json')"))
for source in ('app.html','app.js','styles.css','brand.js','brand.css','manifest.webmanifest'):
 shutil.copy2(repo/'web'/source,root/source)
(root/'brand').mkdir(exist_ok=True);shutil.copy2(repo/'web/brand/allure-logo.png',root/'brand/allure-logo.png')
config={'cleanUrls':True,'redirects':[{'source':'/story','destination':'/','permanent':False}], 'rewrites':[{'source':'/api/v1/:path*','destination':origin+'/api/v1/:path*'},{'source':'/assets/downloads/:path*','destination':origin+'/assets/downloads/:path*'}], 'headers':[{'source':'/assets/:path*','headers':[{'key':'Cache-Control','value':'public, max-age=86400'}]}]}
(root/'vercel.json').write_text(json.dumps(config,indent=2))
manifest=[{'file':str(p.relative_to(root)),'path':str(p.resolve()),'sha':hashlib.sha1(p.read_bytes()).hexdigest(),'size':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file()]
(root.parent/'allure-deployment-manifest.json').write_text(json.dumps(manifest))
print(f'{len(manifest)} public files, {len(public)} reference images. API requests proxy to {origin}.')
