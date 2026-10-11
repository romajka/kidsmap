import json,csv,sys
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
h=Path(__file__).parent
key=lambda r:(r['role'],r['language'],r['width'],r['scene'])
data=json.loads((h/'visual-matrix.result.txt').read_text(encoding='utf-8'))
rows={key(r):{**r,'evidence':'visual-matrix.result.txt'} for r in data['rows']}
for filename in ['create-state-matrix.result.txt','admin-render-proof.result.txt','empty-before-keyboard.result.txt']:
 for r in json.loads((h/filename).read_text(encoding='utf-8'))['rows']:rows[key(r)]={**r,'evidence':filename}
result=list(rows.values())
for r in result:
 if r['role']=='moderator' and r['language'] in ['az','en'] and r['scene'] in ['admin-create','admin-edit']:
  r['geometry_status']=r['status'];r['copy_status']='FAIL';r['status']='FAIL';r['finding']='ORG-QA-04';r['copy_evidence']='admin-copy.result.txt'
 if r['role']=='moderator' and r['width']==1024 and r['scene']=='admin-selection':r['finding']='ORG-QA-03'
(h/'matrix.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
with (h/'matrix.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=['role','language','width','scene','status','screenshot','evidence','error']);writer.writeheader()
 writer.writerows({k:r.get(k,'') for k in writer.fieldnames} for r in result)
summary={'rows':len(result),'statuses':dict(Counter(r['status'] for r in result)),'console_messages':dict(Counter(e['message'] for e in data['errors'])),'page_errors':[e for e in data['errors'] if e['type']=='pageerror'],'blocked_external_origins':data['blockedExternalOrigins'],'replaced_rows':108,'note':'Fresh stable-disclosure/empty-state and actual-admin-field probes supersede erroneous generic heuristics; raw attempts retained.'}
(h/'matrix-summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
print('Remaining non-PASS',[(r['role'],r['language'],r['width'],r['scene'],r.get('error','')[:150]) for r in result if r['status']!='PASS'])
