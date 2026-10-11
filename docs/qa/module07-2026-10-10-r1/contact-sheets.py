"""Derived contact sheets for human inspection. Original PNGs stay unchanged."""
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;S=P/'screenshots';O=P/'visual-review';O.mkdir(exist_ok=True)
for state in ['login','register','settings','team','deletion','reset-open','google-local-error','deletion-code-error','deletion-scheduled','deletion-canceled','organization-team-filled','place-team-filled']:
 files=[(lang,width,S/f'{state}-{lang}-{width}.png') for lang in ['ru','az','en'] for width in [360,390,768,1024,1280,1440]]
 files=[x for x in files if x[2].exists()]
 if not files:continue
 canvas=Image.new('RGB',(1800,780*3),'#e6e6e6');d=ImageDraw.Draw(canvas)
 for lang,width,f in files:
  index=['ru','az','en'].index(lang)*6+[360,390,768,1024,1280,1440].index(width);x=(index%6)*300;y=(index//6)*780
  im=Image.open(f).convert('RGB');im=im.crop((0,0,im.width,min(im.height,1500)));im.thumbnail((294,735));canvas.paste(im,(x+(300-im.width)//2,y+35));d.text((x+5,y+5),f'{state} {lang} {width}px',fill='black')
 canvas.save(O/(state+'.jpg'),quality=90)
print('Derived contact sheets',len(list(O.glob('*.jpg'))))
