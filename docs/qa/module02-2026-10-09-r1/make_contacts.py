from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import json,hashlib
h=Path(__file__).parent
out=h/'contact-sheets';out.mkdir(exist_ok=True)
files=list((h/'screenshots').glob('*.png'))
manifest=[]
for p in files:
 im=Image.open(p);manifest.append({'file':p.relative_to(h).as_posix(),'width':im.width,'height':im.height,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for lang in ['ru','az','en']:
 for width in [360,390,768,1024,1280,1440]:
  selection=sorted(p for p in files if f'-{lang}-{width}-' in p.name)
  if not selection:continue
  sheet=Image.new('RGB',(1440,390*((len(selection)+3)//4)), '#edf1ed');draw=ImageDraw.Draw(sheet)
  for i,p in enumerate(selection):
   image=Image.open(p).convert('RGB');thumb=ImageOps.contain(image,(348,350));x=(i%4)*360;y=(i//4)*390
   sheet.paste(thumb,(x+(360-thumb.width)//2,y+30));draw.text((x+5,y+5),p.stem.replace(f'-{lang}-{width}','')[:45],fill='black')
  sheet.save(out/f'{lang}-{width}.jpg',quality=88)
(h/'screenshots-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Fresh screenshots',len(manifest),'sheets',len(list(out.glob('*.jpg'))))
