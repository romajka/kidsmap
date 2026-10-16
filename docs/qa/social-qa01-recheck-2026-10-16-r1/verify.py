"""Bounded preservation and evidence gate. No product writes."""
import ast,hashlib,json,subprocess,urllib.request
from pathlib import Path
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
entry=json.loads((H/'entry.json').read_text());allowed={'docs/qa/continuation-and-repair-prompts-2026-10-11.md'}
changed=[];missing=[]
for n,v in entry['files'].items():
 p=R/n
 if not p.exists():missing.append(n)
 elif digest(p)!=v:changed.append(n)
current=[json.loads(line)for line in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]
containers={c['ID']:c for c in current};container_drift=[]
for old in entry['containers']:
 now=containers.get(old['ID'])
 if now is None or any(now[k]!=old[k]for k in ('Names','Ports','State')):container_drift.append(old['Names'])
processes=[]
for old in entry['foreign_processes']:
 p=Path('/proc')/str(old['pid'])
 try:matches=[a.decode()for a in(p/'cmdline').read_bytes().split(b'\0')if a]==old['args']
 except OSError:matches=False
 processes.append({'pid':old['pid'],'same_argv':matches})
meta=json.loads((H/'server-current.json').read_text());source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=10))
(H/'runtime-source-final.json').write_text(json.dumps(source,indent=2))
state=json.load(urllib.request.urlopen(meta['url']+'/qa/state/',timeout=5));(H/'state-final.json').write_text(json.dumps(state,indent=2))
manifest=[]
for p in sorted((H/'screenshots').glob('*.png')):
 with Image.open(p)as im:dimensions=list(im.size);im.verify()
 manifest.append({'path':str(p.relative_to(H)),'sha256':digest(p),'dimensions':dimensions,'native':True})
(H/'png-manifest.json').write_text(json.dumps(manifest,indent=2))
for p in H.rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
result=json.loads((H/'reproduce-corrected.js.result.json').read_text());rows=result['rows'];commands=[json.loads(l)for l in(H/'commands.jsonl').read_text().splitlines()]
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip();active=[l for l in(R/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')]
baseline=json.loads((H/'runtime-source-baseline.json').read_text());source_match=source['source']==baseline and source['startup_matches_disk']
verification={'mode':'PLAN ONLY SOCIAL-QA-01','application_changes':0,'confirmed_ids':['SOCIAL-QA-01'],'cause':'REVIEW-RATING-READBACK','snapshot':{'root':str(R),'head':head,'branch':branch,'active_run':active,'dirty_worktree':True},'source':{'files':len(baseline),'baseline_current_runtime_match':source_match,'pid_matches':source['pid']==meta['pid'],'template_sha_matches':source['loaded_template_sha256']==digest(R/'src/catalog/templates/catalog/typed_reviews.html'),'locale_paths':source['sole_locale_paths']},'browser':{'complete':result['complete'],'pass':sum(r['status']=='PASS'for r in rows),'fail':sum(r['status']=='FAIL'for r in rows),'cells':'RU390, four types, pending and approved; targeted reproduction only','png_count':len(manifest),'version':result['browser_version'],'diagnostics':result['diagnostics'],'local_unexpected_http_or_js':[]},'preservation':{'entry_file_count':len(entry['files']),'missing':missing,'changed':changed,'allowed_changes':sorted(allowed),'unexpected_changes':sorted(set(changed)-allowed),'head_unchanged':head==entry['head'],'branch_unchanged':branch==entry['branch'],'active_run_unchanged':active==entry['active_run'],'foreign_container_count':len(entry['containers']),'foreign_container_drift':container_drift,'foreign_processes':processes,'foreign_http_continuity':'NOT VERIFIED: five processes disappeared during explicit user interruption; none restarted','foreign_restart':False,'shared_MO_covered_by_entry_hashes':True,'index_byte_baseline':'NOT CAPTURED; no index-mutating commands executed'},'candidate':{'applied':False,'test_methods':7,'tests_run':False,'diff_check_exit':next(x['exit']for x in commands if x['name']=='candidate-diff-check'),'syntax_checked':True},'not_run':['postpatch GREEN','new regression test execution','pending edit/rejected UI','RU/AZ/EN x six-width acceptance','full ACCEPT-09','global corpus','physical devices/screenreader/cross-browser','production and external integrations'],'simulated':['offline external transport blocked during native checks'],'commands':commands,'limits':['initial CLI bootstrap opened login before new isolated contexts installed route blocker; no external integration success claimed','CLI exit0 first reproduce attempt was QA locator failure, observations0; corrected attempt retained separately','browser assertions count observations, not independent defects']}
assert source_match and verification['source']['pid_matches']and verification['source']['template_sha_matches']
assert not missing and not verification['preservation']['unexpected_changes']and not container_drift
assert head==entry['head']and branch==entry['branch']and active==entry['active_run']
assert result['complete']and verification['browser']['pass']==20 and verification['browser']['fail']==8 and len(manifest)==8
for values in state['reviews'].values():
 assert len(values['heads'])==1 and values['heads'][0]['rating']==4 and values['heads'][0]['candidate_id']is None and values['summary']=={'average':4.0,'count':1}
verification['gate']='PASS: plan/evidence/source integrity; confirmed product bug remains OPEN'
(H/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2));print(json.dumps({'gate':verification['gate'],'source':len(baseline),'preserved_entry_files':len(entry['files'])-len(changed),'allowed_changed':changed,'containers':len(entry['containers']),'foreign_http_continuity':'NOT VERIFIED','observations':len(rows),'PNG':len(manifest)},ensure_ascii=False))
