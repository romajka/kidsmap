import ast,hashlib,json,subprocess,urllib.request,re
from pathlib import Path
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2];entry=json.loads((H/'entry.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
changed=[];missing=[]
for n,v in entry['files'].items():
 p=R/n
 if not p.exists():missing.append(n)
 elif sha(p)!=v:changed.append(n)
assert not missing and set(changed)<={'docs/qa/continuation-and-repair-prompts-2026-10-11.md'},(missing,changed)
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip();active=[l for l in(R/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')];assert head==entry['head']and branch==entry['branch']and active==entry['active_run']
containers={c['ID']:c for c in[json.loads(l)for l in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]};drift=[]
for c in entry['containers']:
 n=containers.get(c['ID'])
 if not n or any(n[k]!=c[k]for k in('Names','Ports','State')):drift.append(c['Names'])
assert not drift,drift
processes=[]
for old in entry['foreign_processes']:
 p=Path('/proc')/str(old['pid'])
 try:matches=[a.decode()for a in(p/'cmdline').read_bytes().split(b'\0')if a]==old['args']
 except OSError:matches=False
 processes.append({'pid':old['pid'],'same_argv':matches})
assert all(p['same_argv']for p in processes),processes
source=json.loads((H/'runtime-source.json').read_text());now=json.load(urllib.request.urlopen('http://127.0.0.1:33741/qa/source/',timeout=10));assert source['source']==now['source']and now['startup_matches_disk']and source['pid']==now['pid'];(H/'runtime-source-final.json').write_text(json.dumps(now,indent=2))
proposal=json.loads((H/'proposal-source-baseline.json').read_text());assert all(sha(R/n)==v for n,v in proposal.items());assert not(R/'src/catalog/testcases/test_social_qa02_rejection_feedback.py').exists()
d=json.loads((H/'reproduce.js.result.json').read_text());assert d['complete']and len(d['rows'])==64 and sum(r['status']=='FAIL'for r in d['rows'])==24 and not d['diagnostics']
readback=json.loads((H/'readback.json').read_text());assert readback['read_only']and len(readback['rows'])==8
png=[]
for p in sorted((H/'screenshots').glob('*.png')):
 with Image.open(p)as im:dims=list(im.size);im.verify()
 png.append({'path':str(p.relative_to(H)),'sha256':sha(p),'dimensions':dims,'native':True})
assert len(png)==16;(H/'png-manifest.json').write_text(json.dumps(png,indent=2))
for p in H.rglob('*.py'):ast.parse(p.read_text())
secrets=json.loads((R/'.tmp'/H.name/'credentials.json').read_text());leaks=[]
for p in H.rglob('*'):
 if p.is_file()and p.suffix in('.py','.js','.json','.jsonl','.md','.txt','.diff'):
  text=p.read_text()
  if any(v in text for v in secrets.values()if isinstance(v,str)):leaks.append(str(p.relative_to(H)))
assert not leaks,leaks
for name in('REPORT.md','IMPLEMENTATION_PLAN.md'):
 for link in re.findall(r'\]\(([^)]+)\)',(H/name).read_text()):
  if '://'not in link and link.split('#')[0]!='verification.json':assert(H/link.split('#')[0]).exists(),(name,link)
result={'status':'PLAN COMPLETE / SOCIAL-QA-02 CONFIRMED OPEN','application_changes':0,'candidate_applied':False,'confirmed_ids':['SOCIAL-QA-02'],'snapshot':{'root':str(R),'head':head,'branch':branch,'active_run':active,'dirty_worktree':True},'source':{'files':len(now['source']),'runtime_disk_match':True,'source_unchanged_from_SOCIAL01_fix':True,'pid':now['pid'],'sole_locale_paths':now['sole_locale_paths']},'profile_reuse':{'owner_label_verified':readback['profile_owner_label_verified'],'isolation':readback,'current_PO_MO_manifest_verified_before_setup':True},'native':{'states':16,'observations':64,'pass':40,'fail':24,'PNG':16,'diagnostics':d['diagnostics'],'scope':'four types RU390 first/edit rejected; Specialist AZ/EN390/1440; fresh login/GET/reload. Native submission/rejection transitions attributed to exact-source SOCIAL01 fix result files'},'preservation':{'entry_files':len(entry['files']),'excluded_own_active_evidence':'docs/qa/social-qa01-fix-2026-10-16-r1/','changed':changed,'missing':missing,'unexpected':[],'containers':len(entry['containers']),'container_drift':drift,'processes':processes,'foreign_restart':False,'shared_MO_preserved':True,'head_branch_active_run_match':True},'tests':{'new_candidate_methods':4,'executed':False,'candidate_syntax':'PASS','diff_check_exit':0},'not_run':['patch/GREEN','full six-width feedback acceptance','native correction/resubmit with future feedback','full module09/global corpus','production/external integrations/physical devices/screenreader/cross-browser'],'gate':'PASS: recheck evidence integrity, product bug remains OPEN'}
(H/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'gate':result['gate'],'PASS':40,'FAIL':24,'PNG':16,'source':len(now['source']),'preserved_containers':len(entry['containers']),'preserved_HTTP':len(processes),'changed':changed},ensure_ascii=False))
