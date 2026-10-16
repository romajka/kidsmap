from pathlib import Path
import json,hashlib,csv
from PIL import Image
h=Path(__file__).resolve().parent;r=h.parents[2]
accepted=[]
parts=[('green-v2-ru.js.result.json',lambda x:x['width']==360),('green-v4-ru.js.result.json',lambda x:True),('green-v4-az.js.result.json',lambda x:x['id']!='MOD-QA-11 all note/domain rows unchanged by GET'),('green-v4-en.js.result.json',lambda x:True),('green-roles-v2.js.result.json',lambda x:True),('green-guards-v4.js.result.json',lambda x:True)]
for name,include in parts:
 data=json.loads((h/name).read_text())
 if name!='green-v2-ru.js.result.json':assert data['complete'] is True and not data.get('error')
 for row in data['rows']:
  if include(row):
   assert row['status']=='PASS',(name,row)
   accepted.append({**row,'evidence':name})
(h/'accepted-browser.json').write_text(json.dumps(accepted,ensure_ascii=False,indent=2))
with(h/'accepted-browser.csv').open('w')as f:
 w=csv.DictWriter(f,fieldnames=['id','status','lang','width','model','evidence']);w.writeheader();w.writerows({k:row.get(k)for k in w.fieldnames}for row in accepted)
manifest=[]
for p in sorted((h/'screenshots').glob('*.png')):
 with Image.open(p)as im:im.verify()
 with Image.open(p)as im:dimensions=list(im.size)
 manifest.append({'path':str(p.relative_to(h)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pixels':dimensions,'mode':'SIMULATED CANDIDATE response override/input'if p.name.startswith('CANDIDATE')else'controlled capacity input SIMULATED; actual source'if'capacity'in p.name else'actual source; loading transport/error may be SIMULATED; see row evidence'})
(h/'PNG-manifest.json').write_text(json.dumps(manifest,indent=2))
# Verify complete primary coverage against explicit cells, not just exit codes.
widths=[360,390,768,1024,1280,1440]
for lang in ['ru','az','en']:
 for width in widths:
  cell=[x for x in accepted if x['lang']==lang and x['width']==width]
  for status in ['draft','published']:
   assert any(x['id']=='MOD-QA-10 real '+status+' success and literal name'for x in cell),(lang,width,status)
  for action in ['approve','return','reject']:
   assert any(x['id']=='MOD-QA-11 '+action+' exact escaped reason'for x in cell),(lang,width,action)
   assert any(x['id']=='MOD-QA-11 reviewer '+action+' readable escaped read-only'for x in cell),(lang,width,action)
for lang in ['az','en']:
 for width in [360,1440]:
  for model in ['place','event','specialist']:
   for count in [0,1,2]:assert any(x['lang']==lang and x['width']==width and x['model']==model and x['id']=='MOD-QA-09 native count '+str(count)for x in accepted)
result={'module08':'LOCAL FAIL / MOD12+13 OPEN; approved MOD09–11 CLOSED LOCAL','backend':{'methods':13,'pass':13,'exit':0,'full261_rerun':False},'browser':{'accepted_observations':len(accepted),'pass':len(accepted),'fail':0,'primary_cells':18,'reviewer_cells':18,'counts_az_en_queue_cells':12,'sources':[n for n,_ in parts]},'png':{'count':len(manifest),'manifest':'PNG-manifest.json'},'new_findings':['MOD-QA-12','MOD-QA-13'],'candidate_patches_applied':False,'qa_exclusions':['incorrect initial toast message selector; actual helper uses title','six incorrect modal-focus expectations for inline filter disclosure','status query key and automatic select navigation corrected in QA only','AZ whole-revision comparison affected by own concurrent publication of separate candidate1; terminal reasons and organizations unchanged','failed incomplete-control click expected POST but real control is disabled; corrected to actual guard check','earlier partial guard runs superseded by v4 complete19PASS; prior logs retained'],'production':'NOT RUN','git_push_deployment':'authorized conditionally after module08 readiness; not executed while module08 fails','next_scope':'MOD12/13 plans await explicit approval'}
(h/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
