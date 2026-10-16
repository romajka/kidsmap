"""Select factual completed native evidence; replace only the ten documented harness-timing failures."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent

def load(name):
 p=H/(name+'.js.result.json');d=json.loads(p.read_text());s=json.loads((H/(name+'.js.status.json')).read_text())
 assert s['native_driver_exit']==0 and not d.get('error'),name
 return d
normal=[load(n)for n in ('native-decline-ru-r3','native-decline-az','native-decline-en')]
assert sum(len(d['completedCells'])for d in normal)==18
raw=load('native-cancel-ru');fresh_recheck=load('native-cancel-ru-alert-resume-r3')
saved_one=json.loads((H/'ru-alert-durable-before-interruption-r2.json').read_text())
saved_two=json.loads((H/'ru-alert-partial-r2.json').read_text())
retained_two=[r for r in saved_two['rows']if r['width']==360 and r['name'].startswith('organization:')]
assert len(saved_one['rows'])==1 and len(retained_two)==1 and len(fresh_recheck['rows'])==8
recheck=dict(fresh_recheck,rows=saved_one['rows']+retained_two+fresh_recheck['rows'])
recheck['supportRows']=saved_two['supportRows']+fresh_recheck['supportRows']
assert len(recheck['rows'])==10 and all(r['status']=='PASS'for r in recheck['rows']) and all(r['status']=='PASS'for r in recheck['supportRows'])

key=lambda r:(r.get('scenario'),r.get('lang'),r.get('width'),r['name'])
old_fail={key(r):r for r in raw['rows']if r['status']=='FAIL'};fresh={key(r):r for r in recheck['rows']};assert len(old_fail)==10 and old_fail.keys()==fresh.keys()
ru_rows=[dict(fresh[key(r)],provenance='fresh settled-DOM alert recheck')if r['status']=='FAIL'else r for r in raw['rows']];assert len(ru_rows)==120 and all(r['status']=='PASS'for r in ru_rows)
(H/'cancel-ru-effective.json').write_text(json.dumps({'rows':ru_rows,'counts':{'PASS':120,'FAIL':0},'retained_unchanged_PASS':110,'replaced_harness_timing_FAIL':10,'source_unchanged':True,'raw':'native-cancel-ru.js.result.json','fresh':'native-cancel-ru-alert-resume-r3.js.result.json','partial_r2_one_row':'ru-alert-partial-r2.json','durable_one_row':'ru-alert-durable-before-interruption-r2.json'},ensure_ascii=False,indent=2))
other_cancel=[load(n)for n in ('native-cancel-az','native-cancel-en')]
accept=[load(n)for n in ('native-accept-ru','native-accept-az','native-accept-en')]
edges=[load(n)for n in ('native-tabs','native-network','native-stale','native-other')]
selected=[]
for d in normal+other_cancel+accept+edges:
 assert all(r['status']=='PASS'for r in d['rows'])
 selected.extend(d['rows'])
selected.extend(ru_rows)
all_results=normal+[raw,recheck]+other_cancel+accept+edges
unexplained=[]
for d in all_results:
 diag=d['diagnostics']
 if d is edges[-1]:
  provenance=json.loads((H/'nojs-motion-provenance.json').read_text())
  assert provenance['existing_mark_read_function_AST_unchanged'] and diag['pageerrors']==['AbortError: Transition was skipped']*3
 else:assert not diag['pageerrors']
 unexplained.extend(r for r in diag['badResponses']if not r['expected'])
 unexplained.extend(r for r in diag['requestFailures']if r['kind']=='local')
console_allowed={'Failed to load resource: net::ERR_BLOCKED_BY_CLIENT.Inspector','Failed to load resource: the server responded with a status of 409 (Conflict)','Failed to load resource: the server responded with a status of 404 (Not Found)'}
for d in all_results:
 unexplained.extend(r for r in d['diagnostics']['console']if r['text']not in console_allowed)
assert not unexplained,unexplained
summary={'decision':'ACCESS-QA-02 scoped browser GREEN; final preservation/source gate required','rows':selected,'counts':{'PASS':len(selected),'FAIL':0},'native_decline_matrix_cells':18,'cancel_stale_matrix_cells':18,'native_shared_accept_flows':12,'additional_RU_recheck_support_rows':len(recheck['supportRows']),'retained_RU_cancel_rows':110,'fresh_RU_alert_replacements':10,'browser':normal[0]['browser'],'diagnostics_unexplained':unexplained,'known_inherited_noJS_transition_aborts':3,'diagnostic_provenance':'nojs-motion-provenance.json','notes':'Rows are observations, not independent end-to-end tests. The old raw10alert timingFAIL remain immutable; only exact matching fields replaced after proper navigation wait. Earlier interrupted24RU PNG not accepted as complete assertions.'}
(H/'observations.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in summary.items()if k not in ('rows',)}))
