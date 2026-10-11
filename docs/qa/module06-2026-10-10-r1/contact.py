"""Derived QA contact sheet only; originals remain fresh native screenshots."""
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent/'screenshots'
names=['home-ru-390.png','catalog-ru-390.png','organization-detail-ru-390.png','specialist-detail-ru-390.png','event-detail-ru-390.png','place-long-fallback-ru-390.png','home-en-1440.png','catalog-en-1440.png','organization-detail-az-1440.png','specialist-detail-az-1440.png','event-cancelled-en-1440.png','place-long-fallback-en-1440.png']
out=Image.new('RGB',(1200,1560),'#ffffff');d=ImageDraw.Draw(out)
for i,name in enumerate(names):
 im=Image.open(P/name).convert('RGB');im=im.crop((0,0,im.width,min(im.height,round(im.width*1.2))));im.thumbnail((294,350));x=i%4*300;y=i//4*520;d.text((x+4,y+3),name,fill='black');out.paste(im,(x+3,y+22))
out.save(P/'DERIVED-contact-public.png');print('Derived contact sheet12 originals; no modification of browser PNG.')
