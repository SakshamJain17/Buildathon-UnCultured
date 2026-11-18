"""Approximate dominant garment colour from supplied catalogue images; not skin analysis."""
import json,math,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app import db
palette={'black':(30,30,30),'white':(238,237,232),'beige':(199,181,151),'brown':(112,80,54),'blue':(93,126,163),'navy':(42,52,74),'olive':(104,108,71),'green':(54,102,70),'red':(162,58,55),'pink':(190,132,143),'grey':(130,130,130)}
path=ROOT/'app/data/reference_catalogue.json';items=json.loads(path.read_text())
for p in items:
    file=ROOT/'runtime/assets/products'/(p['id']+'.jpg')
    if not file.exists():continue
    im=Image.open(file).convert('RGB');w,h=im.size
    bounds=(.3,.3,.7,.62) if p['category']=='tops' else (.3,.48,.7,.88) if p['category']=='bottoms' else (.2,.2,.8,.8)
    crop=im.crop(tuple(int(v*(w if i%2==0 else h)) for i,v in enumerate(bounds))).resize((40,40))
    colours=crop.quantize(colors=5).convert('RGB').getcolors(1600)
    if not colours:continue
    colours.sort(reverse=True);color=colours[0][1]
    closest=min(palette,key=lambda k:sum((a-b)**2 for a,b in zip(color,palette[k])))
    p['colors']=[closest];p['estimated_color_hex']='#%02x%02x%02x'%color
    p['color_method']='Approximate central-image colour; lighting, skin, and background can affect it.'
path.write_text(json.dumps(items,indent=2));db.initialize();db.save_products(items)
print('Updated',len(items),'reference colour estimates; no personal complexion analysis.')
