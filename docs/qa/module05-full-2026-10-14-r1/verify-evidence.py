"""Verify executed evidence; an OPEN finding must keep ACCEPT05 FAIL."""
import csv,difflib,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
accepted=['functional.result.json','pricing.result.json','program.result.json','matrix.result.json','schedule.result.json','conditions.result.attempt1791967299.json','program-finish.result.json','conflict.result.attempt1791969128.json','offline-recheck.result.attempt1791968740.json','roundtrip.result.json','recovery.result.json','loading.result.json','activity-archive.result.json','metadata-fallback.result.json','admin-current.result.json','detach.result.json','program-publication.result.json','program-conflicts.result.json','review-price.result.json','admin-viewport.result.json','final-consumers.result.json']
counts=[]
for name in accepted:
 d=json.loads((P/name).read_text());assert not d.get('error'),(name,d.get('error'));assert not d.get('errors'),(name,d.get('errors'));assert all(r['status']=='PASS' for r in d['rows']),name
 counts.append({'file':name,'PASS':len(d['rows']),'FAIL':0,'pageerrors':len(d.get('errors',[]))})
enum=json.loads((P/'enum-localization.result.json').read_text());assert not enum.get('error') and [r['status'] for r in enum['rows']]==['PASS','FAIL','FAIL'];assert len(enum['localeResults'][1]['untranslated'])==9
count=sum(r['PASS'] for r in counts)
d=json.loads((P/'test-discovery.json').read_text());assert d['count']==334 and len(set(d['method_ids']))==334
assert json.loads((P/'module-tests.command.json').read_text())['exit']==0 and 'Ran 334 tests' in (P/'module-tests.txt').read_text()
for n in ['shared-admin-current-source','shared-admin-final-source']:
 assert json.loads((P/(n+'.command.json')).read_text())['exit']==0 and 'Ran 16 tests' in (P/(n+'.txt')).read_text()
assert json.loads((P/'final-state.command.json').read_text())['exit']==0
state=json.loads((P/'final-state.json').read_text());assert len(state['checks'])==14 and all(c['status']=='PASS' for c in state['checks'])
assert json.loads((P/'node-final-syntax.command.json').read_text())['exit']==0
assert json.loads((P/'locale-final-build-v3.command.json').read_text())['exit']==1
assert json.loads((P/'report-source-refresh.command.json').read_text())['exit']==1
assert json.loads((P/'locale-report-build-v4.command.json').read_text())['exit']==0
assert json.loads((P/'report-runtime-v4.command.json').read_text())['exit']==1
q=subprocess.run(['git','diff','--check','--','src/catalog/services/volunteer_places.py','static/js/owner_place_continuous.js'],capture_output=True,text=True);assert q.returncode==0,q.stdout
old=(P/'owner_place_continuous-before-offline.js').read_text();new=(R/'static/js/owner_place_continuous.js').read_text();(P/'repair07-offline.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='approved07-before-offline.js',tofile='approved07-after-offline.js')))
# Exact module-corpus test files still match the09 executed phase snapshot. Foreign owner admin code is reported separately.
phase=json.loads((R/'docs/qa/offer-qa09-fix-2026-10-14-r1/entry-final.json').read_text())['source_files'];testfiles=[]
for label in d['labels']:
 module='.'.join(label.split('.')[:3]);rel='src/'+module.replace('.','/')+'.py'
 if rel not in testfiles:testfiles.append(rel)
assert all(phase[t]==sha(R/t) for t in testfiles)
rows=[]
for lang in ['ru','az','en']:
 for width in [360,390,768,1024,1280,1440]:
  for view in ['owner-filled-two-groups','owner-empty','program-declined','public-filled-two-groups','admin-filled-two-groups']:
   rows.append({'role_state':view,'language':lang,'width':width,'result':'PASS','evidence':'matrix.result.json','phase':'initial functional/declined/two-group snapshot'})
  for view,file in [('recovery-choice','recovery.result.json'),('loading','loading.result.json'),('admin-current-one-group','admin-current.result.json'),('review-price-blocked','review-price.result.json'),('review-ready','review-price.result.json'),('program-conflict','program-conflicts.result.json'),('owner-final-one-group','final-consumers.result.json'),('public-final-one-group','final-consumers.result.json')]:
   rows.append({'role_state':view,'language':lang,'width':width,'result':'PASS','evidence':file,'phase':'later accepted phase; exact source receipt/limits in REPORT'})
 for view in ['tariff-enum-localization']:
  rows.append({'role_state':view,'language':lang,'width':390,'result':'PASS' if lang=='ru' else 'FAIL','evidence':'enum-localization.result.json','phase':'OFFER-QA-10 fresh current PO-v2 defect'})
with (P/'matrix.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
png=[]
for f in sorted((P/'screenshots').glob('*.png')):
 from PIL import Image
 with Image.open(f) as im:size=list(im.size)
 png.append({'file':'screenshots/'+f.name,'sha256':sha(f),'pixels':size,'note':'full-page captures may resize viewport-dependent sidebar; admin-final-1440-viewport is actual desktop verification' if f.name.startswith('admin-current-') else ''})
(P/'png-manifest.json').write_text(json.dumps(png,indent=2))
retained=[]
for name,kind in [('offline-recheck.result.json','actual07 RED corrected by approved same-scope supplement'),('conditions.result.json','QA harness wrong confirm URL'),('conflict.result.json','QA harness missing candidate_version input'),('conflict.result.attempt1791967682.json','QA HTTP expectation409 vs actual422+classified conflict'),('owner-partial.result.json','additional QA path NOT RUN; hidden language input not opened')]:
 x=json.loads((P/name).read_text());retained.append({'file':name,'classification':kind,'PASS':sum(r['status']=='PASS' for r in x.get('rows',[])),'FAIL':sum(r['status']=='FAIL' for r in x.get('rows',[])),'error':x.get('error')})
retained += [{'file':'runtime-v4-failure.txt','classification':'v4 compiled exit0 but foreign PO changed again before startup; stale verification refused, runtime exit1'}, {'file':'owner-partial.result.attempt1791971084.json','classification':'corrected QA path NOT RUN because owned runtime unavailable'}, {'file':'prepare.txt','classification':'environment bootstrap PostgreSQL transient connection; prepare-resume exit0'}, {'file':'locale-final-build-v3.txt','classification':'concurrent foreign RU duplicate input; exit1'}, {'file':'report-source-refresh.txt','classification':'owned runtime refused incomplete v3 locales; exit1'}]
(P/'retained-failures.json').write_text(json.dumps(retained,indent=2))
c={'backend_unique_methods':334,'target09_earlier_methods':12,'target09_overlap_in_corpus':True,'shared_admin_repeated_methods':16,'shared_admin_repeat_runs':2,'accepted_native_assertions':count,'accepted_native_batches':counts,'enum_diagnostic_PASS':1,'enum_diagnostic_FAIL':2,'read_only_checks':14,'matrix_state_cells_PASS':234+1,'matrix_state_cells_FAIL':2,'PNG':len(png),'test_file_hashes':{t:sha(R/t) for t in testfiles}}
(P/'counts.json').write_text(json.dumps(c,indent=2))
snapshot={'path':str(R),'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),'dirty':subprocess.check_output(['git','status','--short'],text=True),'active_run':'NONE' if 'active_run: NONE' in (R/'docs/task33/implementation-status.md').read_text().splitlines()[:12] else 'UNKNOWN'}
assert snapshot['HEAD']=='e4e05cc213b34e2d771ecb854901bfd016d1db51' and snapshot['branch']=='task33-progress' and snapshot['active_run']=='NONE';(P/'snapshot-final.json').write_text(json.dumps(snapshot,indent=2))
v={'module':'05','decision':'FAIL — OFFER-QA-10 OPEN','functional_backend':'PASS in executed334-method phase','accepted_native_assertions':count,'final_native_enum_diagnostic':'1PASS/2FAIL; nine labels in each ofAZ/EN','open_findings':['OFFER-QA-10'],'closed_scoped_ids':['OFFER-QA-%02d'%i for i in range(1,10)],'full_current_checkout_runtime':'BLOCKED current PO drift: v3 duplicate compile failed, v4 compiled but became stale before setup; prior MATCH is phased evidence','current_source_hashes':{'src/catalog/services/volunteer_places.py':sha(R/'src/catalog/services/volunteer_places.py'),'static/js/owner_place_continuous.js':sha(R/'static/js/owner_place_continuous.js')},'shared_MO_preserved':all(phase[k]==sha(R/k) for k in phase if k.startswith('locale/') and k.endswith('.mo')),'active_run':'NONE preserved','foreign_changes':'preserved; hashes/paths in drift reports, no revert','owned_runtime':'latest v4 startup rejected stale locale manifest; process exited; own PostgreSQL retained','PNG':len(png),'native_Program_archive':'NOT RUN/not exposed in supported UI; nativeActivity/Group archives accepted','production':'NOT RUN','next_plan':'docs/superpowers/plans/2026-10-14-offer-qa10-tariff-enum-localization.md'}
assert v['shared_MO_preserved'];(P/'verification.json').write_text(json.dumps(v,indent=2));print(json.dumps({'decision':v['decision'],'backend':334,'native_PASS':count,'enum_FAIL':2,'PNG':len(png)}))
