"""Derived QA review sheets; native originals preserved, only top viewport preview."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import json
P=Path(__file__).resolve().parent;S=P/'screenshots';sources=[]
for state in ['home','catalog','organizations','organization-detail','specialists','specialist-detail','events','event-detail','event-cancelled','place-long-fallback','activity','empty']:
 sheet=Image.new('RGB',(1320,1230),'#eef2ee');draw=ImageDraw.Draw(sheet);items=[]
 for li,lang in enumerate(['ru','az','en']):
  for wi,width in enumerate([360,390,768,1024,1280,1440]):
   name=f'{state}-{lang}-{width}.png'
   with Image.open(S/name) as im:
    crop=(0,0,im.width,min(im.height,950));thumb=ImageOps.contain(im.crop(crop).convert('RGB'),(214,375));x=wi*220+(220-thumb.width)//2;y=li*410+28;sheet.paste(thumb,(x,y))
   draw.text((wi*220+5,li*410+6),f'{state} {lang.upper()} {width}',fill='#102d1f');items.append({'native_source':name,'preview_crop':crop})
 name='DERIVED-review-'+state+'.png';sheet.save(S/name);sources.append({'sheet':name,'kind':'DERIVED top viewport contact review; not new native evidence','sources':items})
(P/'visual-review-sources.json').write_text(json.dumps(sources,indent=2),encoding='utf-8');print('Derived 12 review sheets from 216 fresh native screenshots')
