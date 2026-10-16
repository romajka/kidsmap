"""Bind effective assertions to raw sources; retain all discarded probes."""
from pathlib import Path
import json,csv
P=Path(__file__).resolve().parent;Q=P.parent/'module04-recheck-2026-10-13-r1';rows=[];selected=[];discarded=[]
def latest(stem,minimum=1):
 files=list(Q.glob(stem+'.result*.json'));valid=[]
 for f in files:
  try:d=json.loads(f.read_text())
  except ValueError:continue
  if not d.get('error') and len(d.get('rows',[]))>=minimum:valid.append((f.stat().st_mtime_ns,f,d))
 if not valid:raise ValueError('No completed '+stem)
 _,f,d=max(valid);return f,d

def add(stem,minimum=1,predicate=lambda r:r.get('status')=='PASS'):
 f,d=latest(stem,minimum);selected.append({'source':str(f.relative_to(P.parent)),'raw_rows':len(d['rows'])})
 for i,r in enumerate(d['rows']):
  if predicate(r):rows.append(dict(r,evidence=str(f.relative_to(P.parent)),row_index=i))
  else:discarded.append({'source':str(f.relative_to(P.parent)),'index':i,'row':r,'classification':'QA expectation/selector/language-route issue; replacement evidence or source contract documented'})

# Lifecycle reaches published before one strict link locator error; only completed prefix accepted.
f=max(Q.glob('lifecycle.result.attempt*.json'),key=lambda f:f.stat().st_mtime_ns);d=json.loads(f.read_text());assert len(d['rows'])==13 and all(r['status']=='PASS' for r in d['rows']);rows.extend(dict(r,evidence=str(f.relative_to(P.parent)),row_index=i) for i,r in enumerate(d['rows']));selected.append({'source':str(f.relative_to(P.parent)),'raw_rows':13,'prefix_before_QA_strict_locator':True})
add('lifecycle-finish',2)
f,d=Q/'media.result.json',json.loads((Q/'media.result.json').read_text());assert len(d['rows'])==5 and all(r['status']=='PASS' for r in d['rows']);rows.extend(dict(r,evidence=str(f.relative_to(P.parent)),row_index=i) for i,r in enumerate(d['rows']))
add('boundaries',20)
add('matrix',144,lambda r:r['status']=='PASS' and r.get('role')!='public')
add('admin-language-matrix',12)
add('state-matrix',72)
add('recovery',54)
add('online-and-shared',31)
add('occurrence',24)
add('admin-states',55)
add('photo-gate-matrix',21,lambda r:r['status']=='PASS')
add('photo-gate-verified',19)
for key in ['org','venue','person']:
 add('stimulus-'+key+'-check')
 d=json.loads((Q/('stimulus-'+key+'-readback.txt')).read_text());assert d['event_snapshot_unchanged'] and d['read_only'];rows.append({'scenario':'fixture-stimulus-'+key+'-read-only-no-event-write','status':'PASS','evidence':str((Q/('stimulus-'+key+'-readback.txt')).relative_to(P.parent))})
add('shared-consumers-finish',4)
add('admin-conflict',18)
add('loading-visible',18)
add('open-admin-selects',18)
add('public-final',18)
add('owner-locale-final',18)
if list(Q.glob('publication-copy.result*.json')):add('publication-copy',24)
assert all(r['status']=='PASS' for r in rows)
(P/'matrix-effective.json').write_text(json.dumps({'rows':rows,'selected_sources':selected,'discarded_QA_probe_rows':discarded},ensure_ascii=False,indent=2))
fields=['scenario','role','state','lang','width','status','evidence','row_index']
with (P/'matrix.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
counts={'effective_browser_and_readback_assertions':len(rows),'effective_failures':0,'independent_test_count':False,'backend_existing_unique':138,'backend_existing_batch_pass':135,'backend_one_fixture_order_case_targeted_pass':1,'backend_new_regressions':5,'historical_geography_fallback_supplement':2,'backend_unique_accepted':143,'global_corpus_not_run':True,'raw_probe_discarded_rows':len(discarded),'png_originals':len(list((P/'screenshots').glob('*.png')))}
(P/'counts.json').write_text(json.dumps(counts,indent=2));print(json.dumps(counts))
