"""Preserve captured proof without converting concurrent source drift into PASS."""
import ast,csv,hashlib,json,subprocess
from collections import Counter
from pathlib import Path
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2];entry=json.loads((H/'entry.json').read_text());baseline=json.loads((H/'runtime-source-baseline.json').read_text());source=json.loads((H/'runtime-source-start.json').read_text());drift=json.loads((H/'source-drift-current.json').read_text());assert source['source']==baseline
rows=[];diagnostics=[]
for lang in('ru','az','en'):
 p=H/f'conflict-{lang}.js.result.json';d=json.loads(p.read_text());assert d.get('complete')and len(d['rows'])==24
 for row in d['rows']:rows.append({**row,'evidence_file':p.name})
 diagnostics += [{'evidence_file':p.name,**x}for x in d['diagnostics']]
assert Counter(r['status']for r in rows)=={'PASS':36,'FAIL':36}
assert len({(r['language'],r['width'])for r in rows})==18
transition=[d for d in diagnostics if d['type']=='pageerror'];assert len(transition)==18 and all(d['text']=='InvalidStateError: Transition was aborted because of invalid state. ViewTransition opt-in disabled'for d in transition)
manifest=[]
for p in sorted((H/'screenshots').glob('*.png')):
 with Image.open(p)as im:dims=list(im.size);im.verify()
 manifest.append({'path':str(p.relative_to(H)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'dimensions':dims,'native':True})
assert len(manifest)==18
(H/'png-manifest.json').write_text(json.dumps(manifest,indent=2));(H/'matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
with(H/'matrix.csv').open('w')as f:
 w=csv.DictWriter(f,fieldnames=['language','width','id','status','evidence_file'],extrasaction='ignore');w.writeheader();w.writerows(rows)
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip();active=[l for l in(R/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')];assert head==entry['head']and branch==entry['branch']and active==entry['active_run'];assert hashlib.sha256((R/'.git/index').read_bytes()).hexdigest()==json.loads((H/'index-entry.json').read_text())['sha256']
for name,digest in json.loads((H/'proposal-source-baseline.json').read_text()).items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest
assert not(R/'src/catalog/testcases/test_social_qa03_conflict_recovery.py').exists()
containers={c['ID']:c for c in[json.loads(l)for l in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]};container_drift=[]
for c in entry['containers']:
 n=containers.get(c['ID'])
 if not n or any(n[k]!=c[k]for k in('Names','Ports','State')):container_drift.append(c['Names'])
processes=[]
for old in entry['foreign_processes']:
 p=Path('/proc')/str(old['pid'])/'cmdline'
 try:same=[a.decode()for a in p.read_bytes().split(b'\0')if a]==old['args']
 except OSError:same=False
 processes.append({'pid':old['pid'],'same_argv':same})
mo=[{'path':name,'match':hashlib.sha256((R/name).read_bytes()).hexdigest()==digest}for name,digest in entry['files'].items()if name.startswith('locale/')and name.endswith('.mo')]
for p in H.rglob('*.py'):ast.parse(p.read_text())
secret=json.loads((R/'.tmp'/H.name/'credentials.json').read_text());assert not any(any(v in p.read_text()for v in secret.values()if isinstance(v,str))for p in H.rglob('*')if p.is_file()and p.suffix in('.py','.js','.json','.jsonl','.md','.txt','.diff','.csv'))
v={'decision':'SOCIAL-QA-03 OPEN; REVIEWABLE PLAN READY; CURRENT SOURCE RECHECK REQUIRED BEFORE PATCH','gate':'NOT PASS FOR CURRENT WORKTREE: concurrent application/PO drift; captured reproduction remains bounded valid evidence','snapshot':{'root':str(R),'head':head,'branch':branch,'dirty_worktree':True,'active_run':active},'captured_source':{'files':len(baseline),'startup_manifest_match':True,'template_match_at_start':True,'pid':source['pid'],'sole_locale_paths':source['sole_locale_paths'],'current_worktree_match':False,'current_locale_manifest':'STALE after foreign PO changes; rebuild required'},'reproduction':{'scope':'Specialist on recorded969snapshot only','rendered_cells':18,'observations':72,'control_pass':36,'source_fail':36,'png':18,'real_409':18,'candidate_current_public_preserved_at_each_conflict':True,'known_transition_pageerrors':len(transition),'introduction':'UNKNOWN; same signature previously seen in SOCIAL01','permanent_data_loss':'NOT CLAIMED'},'candidate':{'application_files':['src/catalog/controllers/typed_reviews.py','src/catalog/templates/catalog/typed_reviews.html','src/catalog/testcases/test_social_qa03_conflict_recovery.py'],'existing_two_files_still_match_proposal_baseline':True,'new_methods':6,'tests':'NOT RUN','applied':False,'approval':'PENDING; fresh source/MO +targeted RED required before approved patch'},'source_drift':drift,'preservation':{'entry_files':len(entry['files']),'whole_worktree_unchanged':'NOT VERIFIED; gate detected concurrent outside-scope changes','index_head_branch_active_run_match':True,'shared_MO':mo,'entry_containers':len(entry['containers']),'container_drift':container_drift,'entry_http_now':processes,'foreign_restart_commands':0,'historical_limits':'Earlier and latest explicit interruptions may stop HTTP; no continuity claim, no foreign restart'},'not_run':['current changed-source recheck','new6candidate tests','SOCIAL03 implementation/acceptance','other3types rendered409 before patch','SOCIAL04-09','full ACCEPT09/global corpus','production/commit/push/deploy','physical devices/cross-browser/screenreader/external integrations'],'simulated':['external font transport blocked'],'commands':'commands.jsonl; failed gates retained','exact_own_secret_leaks':0}
(H/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2));print(json.dumps({'decision':v['decision'],'captured_source':len(baseline),'current_source_match':False,'pass':36,'fail':36,'png':18,'outside_existing_source_changes':len(drift['changed_existing_source']),'new_source_files':len(drift['new_source']),'container_drift':container_drift,'HTTP':processes},ensure_ascii=False))
