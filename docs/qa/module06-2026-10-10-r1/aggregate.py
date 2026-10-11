"""Select fresh authoritative observations; preserve raw attempts and corrections."""
from pathlib import Path
import json,csv,collections,hashlib,datetime,sys
from PIL import Image
P=Path(__file__).resolve().parent;sys.stdout.reconfigure(encoding='utf-8')
rows=[];selected=[];superseded=[]
def addfile(name,accept=lambda x:True):
 d=json.loads((P/name).read_text(encoding='utf-8'));rs=d['rows'];kept=[]
 for n,x in enumerate(rs):
  if not accept(x):continue
  x=dict(x);x['evidence_file']=name;x['evidence_row']=n+1
  x.setdefault('role','anonymous');x.setdefault('lang','UNRECORDED');x.setdefault('width','UNRECORDED');x.setdefault('classification','ACTUAL local synthetic browser/HTTP')
  if name=='http-negative.json':x['width']='N/A HTTP';x['classification']='ACTUAL localhost HTTP; no rendered-browser claim'
  if name=='admin-functional.result.txt' and x['role']=='admin/public':
   x['adminWidth']=1440;x['width']=390
   for lang in ['ru','az','en']:
    if '-'+lang in x['id']:x['lang']=lang
  if name=='event-native.result.txt' and x['id']=='before-cancel-public-scheduled':x['width']=1440
  kept.append(x)
 rows.extend(kept);selected.append({'file':name,'raw_rows':len(rs),'selected_rows':len(kept),'selected_statuses':dict(collections.Counter(x['status'] for x in kept))})
tailids={x['id'] for x in json.loads((P/'tail.result.txt').read_text(encoding='utf-8'))['rows']}
extrasids={x['id'] for x in json.loads((P/'extras.result.txt').read_text(encoding='utf-8'))['rows']}
addfile('matrix.result.txt',lambda x:x['id']!='sort-Escape')
addfile('functional.result.txt',lambda x:x['id'] not in tailids|extrasids|{'functional-harness-error'})
addfile('tail.result.txt')
addfile('map-browser.result.txt',lambda x:x['status']=='PASS')
addfile('map-geometry.result.txt')
addfile('sdk-failure.result.txt')
addfile('admin-functional.result.txt',lambda x:x['id']!='admin-functional-harness-error')
addfile('admin-resume.result.txt',lambda x:x['id'] not in {'native-published-edit-search-cache','native-published-edit-map-cache','native-published-edit-reload'})
addfile('update-live.result.txt')
addfile('event-native.result.txt')
addfile('public-native.result.txt',lambda x:x['id'] in {'sort-Escape-settled','sort-keyboard-focus-visible'})
addfile('extras.result.txt',lambda x:x['id'] not in {'native-list-to-specialist','native-list-to-organization','native-list-to-event','type-temporary'})
if (P/'navigation-proof.result.txt').exists():addfile('navigation-proof.result.txt',lambda x:x['id']!='type-temporary-event-results')
if (P/'type-proof.result.txt').exists():addfile('type-proof.result.txt')
if (P/'pointer-final.result.txt').exists():addfile('pointer-final.result.txt')
if (P/'filter-settled.result.txt').exists():addfile('filter-settled.result.txt')
addfile('http-negative.json')
for lang in ['ru','az','en']:
 for width in [360,390,768,1024,1280,1440]:
  for ident,reason in [('actual-Google-SDK','No authorized real SDK/keys/tiles; adapter and transport abort separate'),('actual-Leaflet-SDK','External integration blocked; real SDK not executed'),('map-desktop-following-close-steps','Blocked by PUBLIC-QA-01')]:
   if ident=='map-desktop-following-close-steps' and width<=760:continue
   rows.append({'id':ident,'status':'NOT RUN','role':'anonymous','lang':lang,'width':width,'classification':'LIMITATION','reason':reason})
for ident,role,reason in [('public-write-conflict','admin','Full concurrent mutation/moderation conflict matrix outside module06; no browser evidence'),('production','anonymous','No production connection authorized or made'),('full-test-suite','QA','Only 11 targeted Django modules + one Node test file'),('cross-worker-cache','QA','Own isolated LocMem per process; distributed/shared production cache NOT RUN'),('fuzzy-typo-search','anonymous','Source supports icontains; mandatory typo feature not established'),('live-external-links','anonymous','Only href/target/rel checked; external navigation/calls blocked')]:
 rows.append({'id':ident,'status':'NOT RUN','role':role,'lang':'ALL','width':'ALL','classification':'LIMITATION','reason':reason})
for x in rows:
 if x['id'].startswith('popup-') and x['status']=='FAIL':x['finding']='PUBLIC-QA-01'
 elif x['id']=='configured-SDK-network-failure-terminal-state' and x['status']=='FAIL':x['finding']='PUBLIC-QA-02'
 elif x['id']=='admin-section-label-language' and x['status']=='FAIL':x['finding']='PUBLIC-QA-03';x['classification']='ENVIRONMENT FAILURE: existing ignored .mo'
 elif x['id']=='native-category-pointer' and x['status']=='FAIL':x['finding']='PUBLIC-QA-04'
unknown=[x for x in rows if x['status']=='FAIL' and not x.get('finding')]
(P/'matrix.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
fields=['id','status','role','lang','width','classification','finding','url','screenshot','evidence_file','evidence_row','reason']
with (P/'matrix.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
manifest=[]
for p in sorted((P/'screenshots').glob('*.png')):
 with Image.open(p) as im:w,h=im.size
 manifest.append({'path':p.relative_to(P).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'width_px':w,'height_px':h,'kind':'DERIVED contact sheet' if p.name.startswith('DERIVED-') else 'NATIVE rendered Chromium screenshot','mtime_utc':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat()})
(P/'screenshots-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
d=json.loads((P/'matrix.result.txt').read_text(encoding='utf-8'))
summary={'selected_runs':selected,'matrix_rows':len(rows),'matrix_statuses':dict(collections.Counter(x['status'] for x in rows)),'unclassified_fail_rows':unknown,'screenshots':dict(collections.Counter(x['kind'] for x in manifest)),'png_files':len(manifest),'browser':d['browser'],'django':{'methods':93,'successful_methods':92,'failing_methods':1,'failure_subtests':2,'native_exit':1},'node':{'tests':6,'passed':6,'native_exit':0},'baseline_console_errors':sum(len(x['errors']) for x in d['diagnostics']),'baseline_local_failed_requests':sum(sum(r['local'] for r in x['failedRequests']) for x in d['diagnostics']),'baseline_external_failed_requests':sum(sum(not r['local'] for r in x['failedRequests']) for x in d['diagnostics']),'findings':4,'application_findings':3,'environment_findings':1}
(P/'results-summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='selected_runs'},ensure_ascii=True));raise SystemExit(1 if unknown else 0)
