import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
raw=json.loads((P/'matrix.result.json').read_text());gaps=json.loads((P/'matrix-gaps.result.json').read_text());by={r['id']:r for r in raw['rows']};replaced=[]
for r in gaps['rows']:
 assert by[r['id']]['status']=='NOT RUN' and r['status']=='PASS';by[r['id']]=r;replaced.append(r['id'])
rows=list(by.values());assert len(rows)==288 and len({r['id'] for r in rows})==288 and all(r['status']=='PASS' for r in rows)
assert not raw['errors'] and not gaps['errors']
assert all(x['status']==400 and x['url'].endswith('/account/organizations/create/') for x in raw['network'])
out={'rows':rows,'raw_run':'matrix.result.json','gaps_run':'matrix-gaps.result.json','raw_pass':252,'raw_NOT_RUN':36,'corrected_only_gaps':replaced,'effective_pass':288,'pageerrors':0,'expected_invalid_URL_HTTP400':len(raw['network']),'console_events':raw['consoleEvents'],'blocked_external_origins':raw['blockedExternalOrigins']}
(P/'matrix-effective.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('Effective matrix288 PASS; original36 NOT RUN retained; only affected gaps rerun')
# Diagnostic contact sheets; original native browser PNGs remain unchanged.
from PIL import Image,ImageDraw,ImageFont
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
for role in ('owner','guest','moderator'):
 for lang in ('ru','az','en'):
  selected=[r for r in rows if r['role']==role and r['lang']==lang];cols=5;cellw=300;cellh=225
  sheet=Image.new('RGB',(cols*cellw,((len(selected)+cols-1)//cols)*cellh),'#edf1ee');draw=ImageDraw.Draw(sheet)
  for i,r in enumerate(selected):
   x=(i%cols)*cellw;y=(i//cols)*cellh
   with Image.open(P/r['screenshot']) as im:
    im=im.convert('RGB');im.thumbnail((cellw-8,cellh-28));sheet.paste(im,(x+(cellw-im.width)//2,y+24))
   draw.text((x+5,y+4),r['scene']+' / '+str(r['width']),font=font,fill='#172a20')
  dest=P/'contact-sheets';dest.mkdir(exist_ok=True);sheet.save(dest/(role+'-'+lang+'.png'))
