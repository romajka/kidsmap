"""Manifest and visual overview of original PNG evidence; no evidence deletion."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;Q=P.parent/'module03-spec-fix-2026-10-13-r1'
manifest=[]
for base in (Q,P):
 for f in sorted((base/'screenshots').glob('*.png')):
  with Image.open(f) as im:size=im.size
  manifest.append({'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'size':size})
(P/'png-manifest.json').write_text(json.dumps(manifest,indent=2))
for base in (Q,P):
 files=sorted((base/'screenshots').glob('*.png'))
 for batch in range(0,len(files),48):
  subset=files[batch:batch+48];out=Image.new('RGB',(1440,240*((len(subset)+5)//6)),'white');d=ImageDraw.Draw(out)
  for n,f in enumerate(subset):
   with Image.open(f) as im:
    im=im.convert('RGB');im.thumbnail((232,208));x=(n%6)*240;y=(n//6)*240;out.paste(im,(x,y));d.text((x+2,y+211),f.name[:33],fill='black')
  out.save(P/f'overview-{base.name}-{batch//48:02}.jpg',quality=88)
print('Original PNGs packaged:',len(manifest))
