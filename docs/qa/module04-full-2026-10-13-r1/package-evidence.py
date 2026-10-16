"""Package native originals; derived contact sheet is only a navigation aid."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageOps,ImageDraw
P=Path(__file__).resolve().parent
rows=[]
for f in sorted((P/'screenshots').glob('*.png')):
 with Image.open(f) as im:width,height=im.size
 rows.append({'path':'screenshots/'+f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size,'width':width,'height':height,'native_original':True})
(P/'png-manifest.json').write_text(json.dumps(rows,indent=2))
names=['owner-empty-step1-en-390.png','specialist-filled-step1-az-390.png','admin-new-ru-390.png','photo-clear-verified-ru-390.png','state-conflict-en-390.png','state-loading-en-390.png','recovery-network-az-390.png','public-published-ru-1440.png']
canvas=Image.new('RGB',(800,4*650),'#e9eef1');draw=ImageDraw.Draw(canvas)
for i,name in enumerate(names):
 f=P/'screenshots'/name
 if not f.exists():continue
 with Image.open(f) as im:
  cropped=im.convert('RGB').crop((0,0,im.width,min(im.height,1400)));cropped.thumbnail((380,600));x=(i%2)*400+10;y=(i//2)*650+30;canvas.paste(cropped,(x,y));draw.text((x,y-20),name,fill='black')
canvas.save(P/'visual-overview.jpg',quality=90)
print(json.dumps({'png_originals':len(rows),'derived_overview':True}))
