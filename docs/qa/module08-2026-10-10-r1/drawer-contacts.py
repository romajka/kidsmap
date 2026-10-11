from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;rows=json.loads((P/'drawers.result.txt').read_text(encoding='utf-8'))['rows'];font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',13)
manifest=json.loads((P/'contacts-manifest.json').read_text(encoding='utf-8'))
for lang in ['ru','az','en']:
 files=list(dict.fromkeys(r['screenshot'] for r in rows if r.get('lang')==lang and r.get('screenshot')));canvas=Image.new('RGB',(960,36+264*((len(files)+2)//3)),'#e4e8ec');draw=ImageDraw.Draw(canvas);draw.text((10,8),f'DERIVED | open admin filters {lang.upper()} | 6 widths x 3 queues',font=font,fill='black')
 for n,f in enumerate(files):
  with Image.open(P/'screenshots'/f) as im:im=im.convert('RGB');im.thumbnail((312,238));x=(n%3)*320+4;y=36+(n//3)*264;canvas.paste(im,(x,y));draw.text((x,y+239),f[:45],font=font,fill='black')
 path=P/'contacts'/f'filters-{lang}.png';canvas.save(path);manifest=[r for r in manifest if r['path']!=path.relative_to(P).as_posix()];manifest.append({'path':path.relative_to(P).as_posix(),'native_inputs':files,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'classification':'DERIVED overview of native open filters'})
(P/'contacts-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print('DERIVED sheets',len(manifest))
