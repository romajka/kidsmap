from collections import Counter
from pathlib import Path
from PIL import Image
p=Path('/mnt/c/kidsmap/docs/qa/site-qa06-fix-2026-10-18-pc-r1/png/smoke-final-branding-rejected-content-ru-390.png')
im=Image.open(p).convert('RGB');c=Counter(im.crop((95,380,337,523)).getdata());greens=[(n,rgb) for rgb,n in c.items() if rgb[1]>rgb[0]+30 and rgb[1]>rgb[2]+20];greens.sort(reverse=True)
def lum(rgb):
 vals=[v/255 for v in rgb];vals=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in vals];return sum(a*b for a,b in zip(vals,[.2126,.7152,.0722]))
for n,rgb in greens[:3]:print({'rgb':rgb,'pixels':n,'contrast_against_white':round(1.05/(lum(rgb)+.05),2)})
