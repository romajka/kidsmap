"""Contact sheets of original QA screenshots for visual inspection, not rendered evidence."""
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent
for kind in ['owner-filled','admin-filled','admin-error','owner-long']:
 files=[P/'screenshots'/f'{kind}-{lang}-{width}.png' for lang in ['ru','az','en'] for width in [360,390,768,1024,1280,1440]]
 sheet=Image.new('RGB',(1500,1200),'white');draw=ImageDraw.Draw(sheet)
 for i,file in enumerate(files):
  if not file.exists():continue
  im=Image.open(file).convert('RGB');im.thumbnail((245,365));x=(i%6)*250;y=(i//6)*400;sheet.paste(im,(x,y+20));draw.text((x+3,y+3),file.stem,fill='black')
 sheet.save(P/(kind+'-contact-sheet.png'))
print('4 derived contact sheets; original PNGs retained')
