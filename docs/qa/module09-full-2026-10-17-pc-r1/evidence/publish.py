import json,re,hashlib,csv,shutil
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
Q=Path(__file__).resolve().parent;R=Q.parents[1];O=R/'docs/qa/module09-full-2026-10-17-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=list(Q.glob('matrix-*.json'));assert len(files)==8
matrix=[r for p in sorted(files) for r in json.loads(p.read_text())['rows']]
assert sum(r['id'].endswith('-render') for r in matrix)==810
assert not [r for r in matrix if r['status']!='PASS' and not r['id'].endswith('-single-main-landmark')]
# Classify observations without rewriting original statuses.
classified=[]
for row in matrix:
 r=dict(row)
 if r['status']=='FAIL':
  r['classification']='SOCIAL-QA-11' if r.get('mainCount')==2 else 'EXCLUDED-absence-alone-not-confirmed-defect'
 classified.append(r)
functional_names=['flows','flows-complete','decisions','edits','site-finish','favorites-notifications','favorites-finish','recovery','adjacent-feed','extra-invites','loading']
functional=[]
for name in functional_names:
 data=json.loads((Q/(name+'.json')).read_text())
 functional.extend(dict(r,artifact=name+'.json') for r in data['rows'])
assert sum(r['status']=='FAIL' for r in functional)==19
assert all(r['id']=='anonymous-notifications-login-recovery' or r['id']=='employee-reply-scope-activity' for r in functional if r['status']=='FAIL')
raw=matrix+functional
summary={'utc':datetime.now(timezone.utc).isoformat(),'module_status':'OPEN','acceptance':'FAIL: SOCIAL-QA-10 P2 + SOCIAL-QA-11 P3','source_files':1024,'backend':{'full_once':{'methods':168,'exit':1,'failures':0,'errors':10,'passed':158,'reason':'Missing original guard module in TCP profile'},'socket_targeted':{'methods':11,'exit':0,'failures':0,'errors':0,'passed':11,'scope':'10 blocked methods + 1 migration method'},'unique_methods':169,'unique_final_passed':169,'total_method_executions':179,'assertions_changed':False},'matrix':{'roles':8,'languages':['ru','az','en'],'widths':[360,390,768,1024,1280,1440],'screens':810,'raw_observations':len(matrix),'raw_statuses':dict(Counter(r['status'] for r in matrix)),'confirmed_SOCIAL11_observations':sum(r.get('classification')=='SOCIAL-QA-11' for r in classified),'excluded_structural_observations':sum(r.get('classification','').startswith('EXCLUDED') for r in classified),'unhandled_pageerrors':sum(len(r.get('errors',[])) for r in matrix),'unexpected_local_http':sum(len(r.get('localBad',[])) for r in matrix),'console_messages':sum(len(r.get('consoleErrors',[])) for r in matrix),'blocked_external_requests':sum(r.get('externalBlocked',0) for r in matrix),'expected403_console':18},'functional_raw':{'observations':len(functional),'statuses':dict(Counter(r['status'] for r in functional)),'per_package':{n:dict(Counter(r['status'] for r in functional if r['artifact']==n+'.json')) for n in functional_names}},'all_raw_observations':len(raw),'all_raw_statuses':dict(Counter(r['status'] for r in raw)),'readback':json.loads((Q/'extra-readback-v2.json').read_text()),'not_run':['physical devices','real screenreader','cross-browser','real OAuth/SMTP/CDN integrations','production','global full-project suite','Place/Specialist stale-reaction native screenshots after2Chromium capture errors'],'simulated':['network failure favorites','delayed/503 favorite transport','blocked external browser requests'],'finding_ids':['SOCIAL-QA-10','SOCIAL-QA-11']}
assert summary['matrix']['confirmed_SOCIAL11_observations']==486 and summary['matrix']['excluded_structural_observations']==54
(O/'results-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
(O/'matrix.json').write_text(json.dumps({'rows':classified,'note':'raw status retained; classification separates confirmed issue from excluded observation'},ensure_ascii=False,indent=2))
with (O/'matrix.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=['role','lang','width','id','status','classification','url']);w.writeheader();w.writerows({k:r.get(k,'') for k in w.fieldnames} for r in classified)
(O/'functional-matrix.json').write_text(json.dumps({'rows':functional},ensure_ascii=False,indent=2))
# Explicit original IDs: union is169, runner outputs kept intact except disposable credentials.
ids=[]
for n in ['tests','socket-tests']:
 ids.extend(re.findall(r'^\w+\s+\((catalog\.[^)]+)\)',(Q/(n+'.log')).read_text(),re.M))
assert len(set(ids))==169,(len(ids),len(set(ids)))
(O/'test-methods.json').write_text(json.dumps(sorted(set(ids)),indent=2))
# Copy current local evidence; do not copy media, browser profiles, session storage or shared artifacts.
E=O/'evidence';E.mkdir(exist_ok=True)
redactions={'<fictional-local-password>':'<fictional-local-password>','<redacted-disposable-key>':'<redacted-disposable-key>'}
for p in Q.iterdir():
 if p.is_file() and p.suffix in {'.py','.js','.json','.jsonl','.log','.txt','.sh','.exit'}:
  t=p.read_text(encoding='utf-8-sig')
  for a,b in redactions.items():t=t.replace(a,b)
  (E/p.name).write_text(t,encoding='utf-8')
shutil.copyfile(Q/'locales/manifest.json',O/'locale-manifest.json')
(O/'png').mkdir(exist_ok=True)
for p in (Q/'png').glob('*.png'):shutil.copyfile(p,O/'png'/p.name)
png={p.relative_to(O).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size,'kind':'native Chromium viewport PNG'} for p in (O/'png').glob('*.png')}
(O/'png-manifest.json').write_text(json.dumps(png,indent=2));summary['png_files']=len(png);summary['png_bytes']=sum(v['bytes'] for v in png.values());(O/'results-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps({'backend_unique':169,'matrix_screens':810,'observations':len(raw),'statuses':summary['all_raw_statuses'],'png':len(png),'bytes':summary['png_bytes']}))
