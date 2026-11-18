"""Two different original motion films composed from the supplied reference photos."""
from pathlib import Path
import json,subprocess
root=Path(__file__).resolve().parents[1]
assets=root/'runtime/assets';films=assets/'films';films.mkdir(parents=True,exist_ok=True)
items=json.loads((root/'app/data/reference_catalogue.json').read_text())
sequences={'feeling':[items[30],items[33],items[36]],'process':[items[0],items[25],items[45]]}
for name,sequence in sequences.items():
    segments=[]
    for i,p in enumerate(sequence):
        image=assets/'products'/(p['id']+'.jpg');out=films/f'{name}-{i}.mp4';segments.append(out)
        vf="scale=800:1200:force_original_aspect_ratio=increase,crop=800:1200,zoompan=z='min(zoom+0.00035,1.08)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=96:s=576x864:fps=24,fade=t=in:st=0:d=0.5,fade=t=out:st=3.5:d=0.5,format=yuv420p"
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(image),'-vf',vf,'-t','4','-c:v','libx264','-preset','fast','-crf','25',str(out)],check=True)
    manifest=films/(name+'.txt');manifest.write_text('\n'.join("file '"+str(p)+"'" for p in segments))
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(manifest),'-c','copy','-movflags','+faststart',str(films/(name+'.mp4'))],check=True)
    for p in segments:p.unlink()
    manifest.unlink()
    print('Created',name+'.mp4',flush=True)
