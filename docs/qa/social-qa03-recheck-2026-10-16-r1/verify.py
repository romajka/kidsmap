import ast,csv,hashlib,json,re,subprocess,urllib.request
from collections import Counter
from pathlib import Path
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;entry=json.loads((H/'entry.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
changed=[];missing=[]
for name,digest in entry['files'].items():
 p=R/name
 if not p.exists():missing.append(name)
 elif sha(p)!=digest:changed.append(name)
assert not missing,missing
foreign_drift=sorted(set(changed)-{'docs/qa/continuation-and-repair-prompts-2026-10-11.md'})
assert all(n.startswith('docs/qa/admin-moderation-audit-2026-10-16-r1/')for n in foreign_drift),foreign_drift
(H/'foreign-artifact-drift.json').write_text(json.dumps({'status':'DETECTED; preserved in place, not overwritten; attribution not verified','files':[{'path':n,'entry_sha256':entry['files'][n],'current_sha256':sha(R/n)}for n in foreign_drift],'application_drift':False,'original_gate':'final-gate.txt; exit1 retained'},indent=2))
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip();active=[l for l in(R/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')];assert head==entry['head']and branch==entry['branch']and active==entry['active_run'];assert sha(R/'.git/index')==json.loads((H/'index-entry.json').read_text())['sha256']
containers={c['ID']:c for c in[json.loads(l)for l in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]};drift=[]
for c in entry['containers']:
 n=containers.get(c['ID'])
 if not n or any(n[k]!=c[k]for k in('Names','Ports','State')):drift.append(c['Names'])
assert not drift,drift
processes=[]
for old in entry['foreign_processes']:
 p=Path('/proc')/str(old['pid']);same=p.exists()and[a.decode()for a in(p/'cmdline').read_bytes().split(b'\0')if a]==old['args'];processes.append({'pid':old['pid'],'same_argv':same})
assert all(p['same_argv']for p in processes),processes
meta=json.loads((H/'server.json').read_text());source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=10));baseline=json.loads((H/'runtime-source-baseline.json').read_text());assert source['source']==baseline and source['startup_matches_disk']and source['pid']==meta['pid'];assert source['loaded_template_sha256']==sha(R/'src/catalog/templates/catalog/typed_reviews.html');assert len(source['sole_locale_paths'])==1 and str(S/'locales')in source['sole_locale_paths'][0];(H/'runtime-source-final.json').write_text(json.dumps(source,indent=2))
rows=[];diagnostics=[];matrix=Counter()
for lang in('ru','az','en'):
 p=H/f'conflict-{lang}.js.result.json';d=json.loads(p.read_text());assert d.get('complete')and len(d['rows'])==24
 for row in d['rows']:row['evidence_file']=p.name;rows.append(row);matrix[(row['language'],row['width'])]+=1
 for event in d['diagnostics']:diagnostics.append({'evidence_file':p.name,**event})
for lang in('ru','az','en'):
 for width in(360,390,768,1024,1280,1440):assert matrix[(lang,width)]==4
assert Counter(r['status']for r in rows)=={'PASS':36,'FAIL':36}
for r in rows:
 if r['status']=='FAIL':assert r['id']in('conflict retains editor and unsaved B for explicit recovery','conflict retains site navigation')
known_transition=[d for d in diagnostics if d['type']=='pageerror'and d.get('text')=='InvalidStateError: Transition was aborted because of invalid state. ViewTransition opt-in disabled']
unexpected=[]
for d in diagnostics:
 if d['type']=='pageerror'and d not in known_transition:unexpected.append(d)
 elif d['type']=='http'and d['status']!=409:unexpected.append(d)
 elif d.get('local')and not(d['type']=='console'and'409'in d['text']):unexpected.append(d)
assert not unexpected,unexpected
manifest=[]
for p in sorted((H/'screenshots').glob('*.png')):
 with Image.open(p)as im:dims=list(im.size);im.verify()
 manifest.append({'path':str(p.relative_to(H)),'sha256':sha(p),'dimensions':dims,'native':True})
assert len(manifest)==18
(H/'png-manifest.json').write_text(json.dumps(manifest,indent=2));(H/'matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
with(H/'matrix.csv').open('w')as f:
 w=csv.DictWriter(f,fieldnames=['language','width','id','status','evidence_file'],extrasaction='ignore');w.writeheader();w.writerows(rows)
for name,digest in json.loads((H/'proposal-source-baseline.json').read_text()).items():assert sha(R/name)==digest
assert not(R/'src/catalog/testcases/test_social_qa03_conflict_recovery.py').exists()
for p in H.rglob('*.py'):ast.parse(p.read_text())
secrets=json.loads((S/'credentials.json').read_text());leaks=[]
for p in H.rglob('*'):
 if p.is_file()and p.suffix in('.py','.js','.json','.jsonl','.md','.txt','.diff','.csv'):
  content=p.read_text()
  if any(v in content for v in secrets.values()if isinstance(v,str)):leaks.append(str(p.relative_to(H)))
assert not leaks,leaks
v={'decision':'SOCIAL-QA-03 CONFIRMED OPEN / PLAN COMPLETE','ids':['SOCIAL-QA-03'],'scope_approval':'PENDING; no application patch','snapshot':{'root':str(R),'head':head,'branch':branch,'dirty_worktree':True,'active_run':active},'source':{'files':len(baseline),'startup_disk_match':True,'loaded_template_match':True,'pid':source['pid'],'sole_locale_paths':source['sole_locale_paths']},'reproduction':{'type':'Specialist shared typed controller','languages':['ru','az','en'],'widths':[360,390,768,1024,1280,1440],'rendered_cells':18,'observations':72,'pass':36,'fail':36,'native_png':18,'real_409':18,'db_candidate_preserved':True,'permanent_data_loss':'NOT CLAIMED; response missing B only','unexpected_local_errors':unexpected,'diagnostic_count':len(diagnostics),'known_shared_transition_pageerrors':known_transition,'transition_introduction':'UNKNOWN; same signature previously observed in SOCIAL01; not fixed'},'candidate':{'application_files':['src/catalog/controllers/typed_reviews.py','src/catalog/templates/catalog/typed_reviews.html','src/catalog/testcases/test_social_qa03_conflict_recovery.py'],'new_methods':6,'tests':'NOT RUN','diff':'proposed.diff','applied':False},'preservation':{'entry_files':len(entry['files']),'changed':changed,'missing':missing,'unexpected_changes':foreign_drift,'application_changes':0,'foreign_QA_artifact_drift':'DETECTED; no claim of whole WORKTREE unchanged','shared_MO_match':True,'index_head_branch_active_run_match':True,'containers':len(entry['containers']),'container_drift':drift,'entry_http':processes,'foreign_restarts':0,'historical_limits':'Earlier HTTP discontinuities remain NOT VERIFIED; current PLAN entry own02 HTTP verified preserved'},'profile':'Fresh own HTTP/cache/media/private-media/email/locales; verified owned fictional02 PostgreSQL reuse; only unused repeat actor pending revisions changed via native UI','not_run':['new6unit regression methods (candidates only)','other3types rendered conflict before patch','SOCIAL03 repair/acceptance','remaining SOCIAL04-09','full ACCEPT09/global corpus','production/commit/push/deploy','physical devices/cross-browser/screenreader/external integrations'],'simulated':['offline external fonts; no network success claimed'],'exact_own_secret_leaks':0,'gate':'PASS WITH LIMITS (source/reproduction/plan; unrelated QA artifact drift and shared transition errors recorded; bug not fixed)'}
(H/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2));print(json.dumps({'decision':v['decision'],'source':len(baseline),'pass':36,'fail':36,'png':18,'entry_files':len(entry['files']),'changed':changed,'entry_http':processes,'containers':len(entry['containers'])},ensure_ascii=False))
