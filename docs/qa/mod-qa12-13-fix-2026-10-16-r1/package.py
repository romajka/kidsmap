import json,hashlib,csv
from pathlib import Path
from PIL import Image
h=Path(__file__).resolve().parent
rows=[]
for n in ['matrix-ru.js.result.json','matrix-az.js.result.json','matrix-en.js.result.json','legacy-fallback.js.result.json']:
 d=json.loads((h/n).read_text());assert d.get('complete')and not d.get('error'),n
 assert all(x['status']=='PASS'for x in d['rows'])
 rows.extend(dict(x,evidence=n)for x in d['rows'])
 for x in d['diagnostics']:
  if x.get('local'):assert n.startswith('matrix-')and ((x['kind']=='requestfailed'and x['error']=='net::ERR_FAILED')or(x['kind']=='console'and x['text']=='Failed to load resource: net::ERR_FAILED')),x
for lang in ['ru','az','en']:
 for width in [360,390,768,1024,1280,1440]:
  cell=[x for x in rows if x['lang']==lang and x['width']==width]
  for status in ['draft','published']:
   for round in [0,1]:assert any(x['id']=='MOD12 real '+status+' success readable round'+str(round)for x in cell)
  assert any(x['id']=='MOD13 burst20 returns and shows newest3'for x in cell)
(h/'accepted-browser.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
with(h/'accepted-browser.csv').open('w')as f:
 w=csv.DictWriter(f,fieldnames=['id','status','lang','width','model','evidence']);w.writeheader();w.writerows({k:x[k]for k in w.fieldnames}for x in rows)
images=[]
for p in sorted((h/'screenshots').glob('*.png')):
 with Image.open(p)as im:im.verify()
 with Image.open(p)as im:dims=list(im.size)
 images.append({'path':str(p.relative_to(h)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pixels':dims,'mode':'RED or GREEN actual source; see observation for SIMULATED inputs/transport/fallback availability'})
(h/'PNG-manifest.json').write_text(json.dumps(images,indent=2))
ledger=json.loads((h/'acceptance-source-ledger.json').read_text());old=json.loads((h.parent/'module08-full-2026-10-16-r1/locale-manifest.json').read_text());new=json.loads((h/'locale-manifest.json').read_text())
a={x['source']:x['po_sha256']for x in old['entries']};b={x['source']:x['po_sha256']for x in new['entries']}
ledger['locale_entries_changed']=[n for n in a if a[n]!=b[n]];ledger['locale_scope']='Only approved MOD09/10 entries; isolated current native MO verified before setup';(h/'acceptance-source-ledger.json').write_text(json.dumps(ledger,indent=2))
assert len(rows)==341
v={'status':'LOCAL PASS scoped MOD12/13; final preservation gate required','ids':{'MOD-QA-12':'CLOSED LOCAL','MOD-QA-13':'CLOSED LOCAL'},'backend_previous':'full261 once +targeted13 retained by source ledger; not rerun','node':{'tests':4,'RED':{'pass':1,'fail':3,'exit':1},'GREEN':{'pass':4,'fail':0,'exit':0}},'browser':{'pass':341,'fail':0,'primary_cells':18,'actual_successful_post':74,'expected_simulated_network_abort':3,'actual_native_publication_sequences':'draft,published,draft,published per cell, without manual clear','burst_input':'SIMULATED 20 notices; real current engine','legacy_input':'SIMULATED engine availability only; actual fallback POST and renderer'},'png':len(images),'source':ledger,'new_findings':[],'NOT_RUN':['repeat full261','all-module corpus','cross-browser/physical devices/screenreader','production in this local QA phase'],'next':'authorized Git package and server release after final preservation gate'}
(h/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2));print(json.dumps({'node':4,'browser':len(rows),'png':len(images),'cells':18}))
