"""DERIVED contact sheets of fresh native screenshots; never substitute native evidence."""
from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;out=P/'contacts';out.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',13);items=[]
main=json.loads((P/'matrix.result.txt').read_text(encoding='utf-8'))['rows']
supp=json.loads((P/'supplement.result.txt').read_text(encoding='utf-8'))['rows']
for lang in ['ru','az','en']:
 for width in [360,390,768,1024,1280,1440]:
  files=list(dict.fromkeys(r['screenshot'] for r in main+supp if r.get('lang')==lang and r.get('width')==width and r.get('screenshot')))
  canvas=Image.new('RGB',(1280,36+math.ceil(len(files)/4)*264),'#e4e8ec');draw=ImageDraw.Draw(canvas);draw.text((10,8),f'DERIVED | module08 {lang.upper()} {width}px | top viewport crops | {len(files)} native frames',font=font,fill='black')
  for n,f in enumerate(files):
   with Image.open(P/'screenshots'/f) as im:
    crop=im.convert('RGB').crop((0,0,im.width,min(im.height,950)));crop.thumbnail((312,238));x=(n%4)*320+4;y=36+(n//4)*264;canvas.paste(crop,(x,y));draw.text((x,y+239),f[:45],font=font,fill='black')
  path=out/f'{lang}-{width}.png';canvas.save(path);items.append({'path':path.relative_to(P).as_posix(),'native_inputs':files,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'classification':'DERIVED overview, top viewport crops only'})
(P/'contacts-manifest.json').write_text(json.dumps(items,indent=2),encoding='utf-8');print('DERIVED sheets',len(items),'input frames',sum(len(x['native_inputs']) for x in items))
