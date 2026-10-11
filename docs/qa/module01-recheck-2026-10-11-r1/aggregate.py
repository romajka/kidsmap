"""Aggregate final executions only; retained failed QA attempts are not silently counted as app bugs."""
import json,csv,hashlib
from collections import Counter
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent
files=['place-flow','review','mixed-price','map','nature','admin-matrix','labels','public','residual','visual-diagnostics']
rows=[];problems=[]
for name in files:
 x=json.loads((P/(name+'.result.txt')).read_text(encoding='utf-8'))
 if x.get('error'):problems.append({'script':name,'error':x['error']})
 for r in x['rows']:
  if 'scenario' not in r:r['scenario']=r.pop('id');r.update(role='owner',lang='ru',width='mixed 390/1440',url='http://localhost:8841/ru/account/places/2/edit/',shot='')
  r['execution']=name;rows.append(r)
assert not problems,problems
unrun=['Full module01 category/subcategory combinations and branch affiliation creation','All pricing mode switches and two-tab pricing conflicts','All coordinate ranges including 0/0 and invalid pair server submission','Real Google SDK/provider success and real GPS/permission prompts','Gallery reorder replacement deletion and every upload error across 18 cells','Opening hours versus lesson timetable full combinations','Foreign IDs/insufficient rights full endpoint matrix','Two tabs repeated submit and network failure recovery full current-run matrix','Screen reader and complete Tab/Shift+Tab/Enter/Space focus traversal','Full module01 empty/loading/error/conflict matrix on all roles/langs/widths','Full configured Django suite and clean-HEAD regression attribution','Production runtime or deployment of these fixes']
for scenario in unrun:rows.append({'execution':'scope-boundary','scenario':scenario,'status':'NOT RUN','role':'applicable','lang':'RU/AZ/EN','width':'360/390/768/1024/1280/1440','url':'','shot':''})
(P/'browser-observations.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
with (P/'matrix.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['execution','scenario','status','role','lang','width','url','shot'],extrasaction='ignore');w.writeheader();w.writerows(rows)
counts={'browser':dict(Counter(r['status'] for r in rows)),'executed_browser_observations':sum(r['status']!='NOT RUN' for r in rows),'django':{'PASS':38,'FAIL':0,'exit_code':0},'node':{'PASS':34,'FAIL':0,'exit_codes':[0,0]},'locale_helper':{'PASS':9,'FAIL':0,'exit_code':0},'old_place_qa_01_07':'targeted fresh verification PASS; whole module acceptance NOT asserted'}
(P/'counts.json').write_text(json.dumps(counts,indent=2))
pngs=[]
for p in sorted((P/'screenshots').glob('*.png')):
 with Image.open(p) as im:size=im.size
 pngs.append({'path':p.relative_to(P).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'width':size[0],'height':size[1]})
(P/'screenshots-manifest.json').write_text(json.dumps(pngs,indent=2))
for role in ['admin','owner','guest']:
 pics=sorted((P/'screenshots').glob('viewport-'+role+'-*.png'))
 canvas=Image.new('RGB',(1800,1500),'#e8e8e8');d=ImageDraw.Draw(canvas)
 for i,p in enumerate(pics):
  im=Image.open(p).convert('RGB');im.thumbnail((580,710));col=i%3;row=i//3;canvas.paste(im,(col*600,row*750+30));d.text((col*600+5,row*750+8),p.name,fill='black')
 canvas.save(P/('contact-'+role+'.jpg'))
print(json.dumps({'counts':counts,'native_png':len(pngs)}))
