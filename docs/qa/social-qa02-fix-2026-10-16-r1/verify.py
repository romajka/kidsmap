"""Final evidence/source/preservation gate for the approved three-file repair."""
import ast,csv,hashlib,json,re,subprocess,urllib.request
from collections import Counter
from pathlib import Path
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
ENTRY=json.loads((H/'entry.json').read_text());ALLOWED={'src/catalog/templates/catalog/typed_reviews.html','docs/qa/continuation-and-repair-prompts-2026-10-11.md','src/catalog/controllers/typed_reviews.py'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
missing=[];changed=[]
for name,digest in ENTRY['files'].items():
 p=R/name
 if not p.exists():missing.append(name)
 elif sha(p)!=digest:changed.append(name)
assert not missing and not set(changed)-ALLOWED,(missing,sorted(set(changed)-ALLOWED))
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip();active=[l for l in(R/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')]
assert head==ENTRY['head'] and branch==ENTRY['branch']and active==ENTRY['active_run']
index=json.loads((H/'index-entry.json').read_text());assert sha(R/'.git/index')==index['sha256']
containers={c['ID']:c for c in[json.loads(l)for l in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]};container_drift=[]
for c in ENTRY['containers']:
 n=containers.get(c['ID'])
 if not n or any(n[k]!=c[k]for k in('Names','Ports','State')):container_drift.append(c['Names'])
assert not container_drift,container_drift
processes=[]
for old in ENTRY['foreign_processes']:
 p=Path('/proc')/str(old['pid'])
 try:matches=[a.decode()for a in(p/'cmdline').read_bytes().split(b'\0')if a]==old['args']
 except OSError:matches=False
 processes.append({'pid':old['pid'],'same_argv':matches})
meta=json.loads((H/'server.json').read_text());source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=10));baseline=json.loads((H/'runtime-source-green-tests.json').read_text());assert source['source']==baseline and source['startup_matches_disk']and source['pid']==meta['pid'];assert source['loaded_template_sha256']==sha(R/'src/catalog/templates/catalog/typed_reviews.html')
(H/'runtime-source-final.json').write_text(json.dumps(source,indent=2))
assert len(source['sole_locale_paths'])==1 and str(S/'locales')in source['sole_locale_paths'][0]
fixture=json.loads((H/'fixtures.json').read_text());states={}
for case in fixture['cases']:states[str(case['id'])]=json.load(urllib.request.urlopen(meta['url']+'/qa/state/'+str(case['id'])+'/',timeout=5))
(H/'state-final.json').write_text(json.dumps(states,indent=2))
for case in fixture['cases']:
 for kind,value in states[str(case['id'])]['reviews'].items():
  assert value['summary']=={'average':2.0,'count':1}
  by_user={h['author_id']:h for h in value['heads']};main=by_user[case['actors']['author']['id']];rejected=by_user[case['actors']['rejected']['id']]
  assert main['rating']==2 and main['current_id']and main['candidate_id']is None and main['revisions'][-1]['status']=='approved'and any(r['rating']==2 and r['status']=='rejected'for r in main['revisions'])
  assert rejected['current_id']is None and rejected['candidate_id']and rejected['candidate_rating']==3 and rejected['revisions'][-1]['status']=='pending'

rows=[];diagnostics=[];accepted=[];excluded=[]
for p in sorted(H.glob('*.js.result.json')):
 d=json.loads(p.read_text())
 assert d.get('complete'),(p.name,d.get('error'))
 assert not any(row['status']=='FAIL'for row in d['rows']),p.name
 accepted.append(p.name)
 for row in d['rows']:row['evidence_file']=p.name;rows.append(row)
 for event in d.get('diagnostics',[]):diagnostics.append({'evidence_file':p.name,**event})
matrix=Counter((r['phase'],r['language'],r['width'],r['kind'])for r in rows if r['phase'].startswith('matrix-'))
expected_states=['first','edit']
for state in expected_states:
 for lang in('ru','az','en'):
  for width in(360,390,768,1024,1280,1440):
   for kind in('place','specialist','activity','event'):assert matrix[('matrix-'+state,lang,width,kind)]==6,(state,lang,width,kind)
manifest=[]
for p in sorted((H/'screenshots').glob('*.png')):
 with Image.open(p)as im:dims=list(im.size);im.verify()
 manifest.append({'path':str(p.relative_to(H)),'sha256':sha(p),'dimensions':dims,'native':True})
(H/'png-manifest.json').write_text(json.dumps(manifest,indent=2));(H/'matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));(H/'excluded-observations.json').write_text(json.dumps(excluded,indent=2))
with(H/'matrix.csv').open('w')as f:
 writer=csv.DictWriter(f,fieldnames=['phase','language','width','kind','case','id','status','evidence_file'],extrasaction='ignore');writer.writeheader();writer.writerows(rows)
unexpected=[d for d in diagnostics if d['type']in('pageerror','http')or d.get('local')]
assert not unexpected,unexpected
for p in H.rglob('*.py'):ast.parse(p.read_text())
secrets=json.loads((S/'credentials.json').read_text());leaks=[]
for p in H.rglob('*'):
 if p.is_file()and p.suffix in('.py','.js','.json','.jsonl','.md','.txt','.diff','.csv'):
  text=p.read_text()
  if any(v in text for v in secrets.values()if isinstance(v,str)):leaks.append(str(p.relative_to(H)))
assert not leaks,leaks
newtest=R/'src/catalog/testcases/test_social_qa02_rejection_feedback.py';candidate=H.parent/'social-qa02-recheck-2026-10-16-r1/candidate/test_social_qa02_rejection_feedback.py';assert newtest.read_bytes()==candidate.read_bytes()
counts=Counter(r['phase']for r in rows);tests=json.loads((H/'test-results.json').read_text());verification={'decision':'SOCIAL-QA-02 CLOSED LOCAL','approved_plan':'docs/qa/social-qa02-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md','ids':['SOCIAL-QA-02'],'snapshot':{'root':str(R),'head':head,'branch':branch,'dirty_worktree':True,'active_run':active},'source':{'files':len(baseline),'tests_runtime_disk_match':True,'template_loaded_disk_match':True,'pid':source['pid'],'sole_locale_paths':source['sole_locale_paths']},'tests':tests,'browser':{'accepted_observations':len(rows),'pass':len(rows),'fail':0,'matrix_states':len(matrix),'matrix_observations':sum(v for v in matrix.values()),'phase_counts':counts,'accepted_result_files':accepted,'png':len(manifest),'diagnostic_count':len(diagnostics),'observed_shared_transition_pageerrors':[d for d in diagnostics if d['type']=='pageerror'],'unexpected_local_errors':unexpected,'simulated_observations':sum(r.get('simulated',False)for r in rows),'known_unchanged_baseline':'SOCIAL03 conflict UI remains outside this approved scope'},'preservation':{'entry_files':len(ENTRY['files']),'changed':changed,'missing':missing,'unexpected_changes':[],'new_application_files':['src/catalog/testcases/test_social_qa02_rejection_feedback.py'],'shared_MO_match':True,'index_sha_match':True,'head_branch_active_run_match':True,'foreign_containers':len(ENTRY['containers']),'container_drift':container_drift,'foreign_processes':processes,'foreign_restart':False,'foreign_process_continuity':'NOT VERIFIED; two entry HTTP absent after observed environment discontinuity','historical_interruption_limit':'Earlier five HTTP continuity remains NOT VERIFIED; during this run two entry HTTP and own HTTP disappeared after model/tool session change. Both foreign same_argv=false are NOT VERIFIED, not PASS. Only own HTTP resumed; details process-interruption.json'},'exact_own_secret_leaks':0,'not_run':['full ACCEPT-09 (once after all module tasks)','other SOCIAL findings acceptance','global corpus','production/commit/push/deploy','physical devices, real screenreader, cross-browser','real SMTP/Google/SDK/other external integrations'],'simulated':['unit cooldown0 (native browser kept real120s)','offline external font/transport block','external fonts blocked; no external integration success claimed'],'gate':'PASS','preservation_limit':'HTTP continuity NOT VERIFIED; no foreign restarts'}
(H/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2));print(json.dumps({'gate':'PASS','preservation_limit':'HTTP continuity NOT VERIFIED; no foreign restarts','decision':verification['decision'],'tests':tests['green']['unique_methods'],'browser':len(rows),'matrix_cells':len(matrix),'png':len(manifest),'changed_entry':changed,'foreign_http':processes,'foreign_containers':len(ENTRY['containers'])},ensure_ascii=False))
