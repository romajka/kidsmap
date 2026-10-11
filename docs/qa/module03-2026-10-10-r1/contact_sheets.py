from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;out=P/'contact-sheets';out.mkdir(exist_ok=True)
groups=['guest-public','admin-filled','admin-directions-open','admin-practice-locations','person-step-1','person-step-2','person-step-3','person-step-5','person-certificates','network-cooperation','state-person-conflict','state-author-errors','state-admin-errors']
for prefix in groups:
 paths=[P/'screenshots'/f'{prefix}-{lang}-{width}.png' for lang in ('ru','az','en') for width in (360,390,768,1024,1280,1440)]
 paths=[p for p in paths if p.exists()]
 if not paths:continue
 canvas=Image.new('RGB',(1440,690*((len(paths)+5)//6)),'#e3e3e3');draw=ImageDraw.Draw(canvas)
 for i,p in enumerate(paths):
  im=Image.open(p).convert('RGB');im.thumbnail((230,655));x=(i%6)*240;y=(i//6)*690
  draw.text((x+3,y+3),p.stem.replace(prefix+'-',''),fill='black');canvas.paste(im,(x+4,y+22))
 canvas.save(out/(prefix+'.jpg'),quality=88)
print('Contact sheets generated',len(list(out.glob('*.jpg'))))
