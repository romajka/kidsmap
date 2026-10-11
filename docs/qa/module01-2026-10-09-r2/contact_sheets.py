from pathlib import Path
from PIL import Image,ImageDraw
here=Path(__file__).resolve().parent
out=here/'contact-sheets';out.mkdir(exist_ok=True)
groups={}
for p in (here/'screenshots').glob('*.png'):
    parts=p.stem.split('-')
    if parts[0] in ('owner','moderator','guest') and parts[-1].isdigit():key='-'.join(parts[:-2])
    elif parts[0]=='deep' and parts[-1].isdigit():key='-'.join(parts[:-2])
    else:continue
    groups.setdefault(key,[]).append(p)
for key,files in groups.items():
    files=sorted(files,key=lambda p:(p.stem.split('-')[-2],int(p.stem.split('-')[-1])))
    canvas=Image.new('RGB',(6*240,((len(files)+5)//6)*665),'#dddddd');draw=ImageDraw.Draw(canvas)
    for i,p in enumerate(files):
        im=Image.open(p);im.thumbnail((238,635));x=(i%6)*240;y=(i//6)*665;canvas.paste(im,(x,y+25));draw.text((x+3,y+5),p.stem,fill='black')
    canvas.save(out/(key+'.jpg'),quality=90)
print('Contact sheets',len(groups))
