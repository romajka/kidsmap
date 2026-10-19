"""PLAN07 source/evidence integrity; metadata PASS does not close source finding."""
import ast,hashlib,itertools,json,re,struct,subprocess
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import urlopen
O=Path(__file__).resolve().parent;R=O.parents[2];Q=R/'.tmp/social07-pc-plan-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True,encoding='utf-8').rstrip('\r\n')
def wsl(*args):return subprocess.check_output(['wsl','-d','Ubuntu-24.04','--',*args],text=True)
e=load(O/'source-entry.json')
assert len(e['sources'])==1021 and all(sha(R/p)==h for p,h in e['sources'].items())
assert load(O/'source-final.json')['sources']==e['sources']
assert all(sha(R/p)==h for p,h in e['shared_mo'].items()) and sha(R/'.cbmignore')==e['cbmignore_sha256']
assert git('rev-parse','HEAD')==e['head']=='852938d96764ae315b92859e3651e5ea62054a36'
assert git('branch','--show-current')==e['branch']=='codex/module09-transfer-2026-10-16-r1'
assert git('rev-parse','HEAD^{tree}')==e['index_tree'] and git('rev-parse','task33-progress')==e['task33_ref']
assert not git('diff','--cached','--name-only')
active=[l for l in (R/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if l.startswith('active_run:')]
assert active==e['active_run']==['active_run: NONE']
oldpaths={l[3:] for l in e['status'].splitlines()};paths={l[3:] for l in git('status','--porcelain=v1','-uall').splitlines()}
assert oldpaths<=paths and all(p in oldpaths or p.startswith(O.relative_to(R).as_posix()+'/') for p in paths)
oldcounts={}
for name,fingerprints in e['prior_packages'].items():
 p=O.parent/name;assert sha(p/'artifact-manifest.json')==fingerprints['manifest_sha256']
 assert sha(p/'verification.json')==fingerprints['verification_sha256']
 manifest=load(p/'artifact-manifest.json');assert all(sha(p/path)==h for path,h in manifest.items()),name
 oldcounts[name]=len(manifest)
assert len(oldcounts)==8

m=load(O/'matrix.json');activity=[r for r in m if r['item']['kind']=='activity'];shared=[r for r in m if r['item']['kind']!='activity']
assert len(m)==66 and len(activity)==48 and len(shared)==18
assert Counter(r['item'].get('variant',r['item']['kind']) for r in m)=={
 'localized':36,'azfallback':6,'snapshot':6,'place':6,'specialist':6,'event':6}
localized=[r for r in activity if r['item']['variant']=='localized']
assert {(r['item']['role'],r['item']['lang'],r['item']['width']) for r in localized}==set(itertools.product(
 ['guest','author'],['ru','az','en'],[360,390,768,1024,1280,1440]))
assert sum(sum(r['controls'].values()) for r in m)==540 and all(all(r['controls'].values()) for r in m)
assert all(len(r['controls'])==9 and len(r['source'])==3 and not any(r['source'].values()) for r in activity)
assert all(len(r['controls'])==6 and not r['source'] for r in shared)
assert sum(sum(not v for v in r['source'].values()) for r in m)==144
assert all(r['before']==r['after'] for r in m)
assert all(not r[k] for r in m for k in ['pageerrors','http_failures','request_failed'])
for r in activity:
 assert r['facts']['detailHeading']==r['item']['expected']
 assert r['facts']['heading']==r['facts']['reloaded'] and 'Activity object (' in r['facts']['heading']
 assert 'Activity object (' in r['facts']['title']
assert len({r['item']['id'] for r in m})==66
log=(O/'tests.log').read_text()
assert (O/'tests.exit').read_text().strip()=='1' and 'Ran 9 tests in 2.769s' in log and 'FAILED (failures=18)' in log
failures=re.findall(r'^FAIL: (test_\w+)',log,re.M)
assert len(failures)==18 and len(set(failures))==7 and not re.search(r'^ERROR:',log,re.M)
ids=re.findall(r'^test_\w+ \(candidate_tests\.SocialQA07TitleTests\.(test_\w+)\)',log,re.M)
assert len(ids)==len(set(ids))==9 and len(set(ids)-set(failures))==2
candidate=load(O/'candidate-manifest.json');controller='src/catalog/controllers/typed_reviews.py';newtest='src/catalog/testcases/test_social_qa07_activity_review_title.py'
assert candidate['scope']==[controller,newtest] and not candidate['applied'] and not (R/newtest).exists()
assert hashlib.sha256((R/controller).read_text(encoding='utf-8').encode()).hexdigest()==candidate['controller_before_normalized_sha256']
assert sha(O/'candidate-typed_reviews.py')==candidate['controller_after_normalized_sha256']
assert sha(O/'candidate_tests.py')==candidate['tests_sha256']==sha(Q/'candidate_tests.py')
assert sha(O/'proposed.diff')==candidate['diff_sha256']
tree=ast.parse((O/'candidate_tests.py').read_text(encoding='utf-8'));methods=[n.name for c in tree.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
assert len(methods)==9 and set(methods)==set(ids)
check=subprocess.run(['git','apply','--check','--ignore-space-change',str(O/'proposed.diff')],cwd=R,capture_output=True,text=True)
assert check.returncode==0,check.stderr
pngs=load(O/'png-manifest.json');assert len(pngs)==114 and len({p['path'] for p in pngs})==114
assert {p.relative_to(O).as_posix() for p in (O/'screenshots').glob('*.png')}=={p['path'] for p in pngs}
for p in pngs:
 raw=(O/p['path']).read_bytes();assert sha(O/p['path'])==p['sha256'] and raw[:8]==b'\x89PNG\r\n\x1a\n' and p['native']
 assert struct.unpack('>II',raw[16:24])==(p['width'],p['height'])
assert all((O/p).is_file() for r in m for p in r['pngs'])
assert all(len(r['pngs'])==2 for r in activity) and all(len(r['pngs'])==1 for r in shared)
info=load(O/'runtime-info.json');assert info==load(O/'live-final.json')
assert info['testing'] and info['source_files']==1021 and info['sole_locales']==['/mnt/c/kidsmap/.tmp/social07-pc-plan-r1/locales/locale']
assert all(e['sources'][p]==h for p,h in info['hashes'].items())
with urlopen('http://127.0.0.1:33347/qa/info/',timeout=10) as response:assert json.load(response)==info
with urlopen('http://127.0.0.1:33347/qa/state/',timeout=10) as response:state=json.load(response)
assert state=={'activities':3,'activity_reviews':0,'place_reviews':0,'specialist_reviews':0,'event_reviews':0}
loc=load(O/'locale-manifest.json');assert loc['status']=='complete' and set(loc['locales'])=={'ru','az','en'}
for r in loc['entries']:
 assert sha(R/'locale'/r['source'])==r['po_sha256']==sha(Q/'locales'/r['snapshot'])
 assert sha(Q/'locales'/r['mo'])==r['mo_sha256'] and r['exit_code']==0
containers=wsl('docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}} {{.Ports}}')
byname=lambda t:{l.split()[1]:l.split()[:3] for l in t.splitlines() if l.strip()}
old,current=byname((O/'containers-entry.txt').read_text()),byname(containers)
assert len(old)==38 and all(current.get(n)==v for n,v in old.items())
assert set(current)-set(old)=={'m09s07-plan-r1-app','m09s07-plan-r1-pg'}
app=json.loads(wsl('docker','inspect','m09s07-plan-r1-app'))[0]
assert app['State']['Running'] and app['HostConfig']['ReadonlyRootfs'] and app['Config']['Labels']['codex.owner']=='social07-pc-plan-r1'
assert set(app['NetworkSettings']['Networks'])=={'m09s07-plan-r1-net'}
assert any(x['Destination']=='/mnt/c/kidsmap' and not x['RW'] for x in app['Mounts'])
assert any(x['Destination']=='/mnt/c/kidsmap/.tmp/social07-pc-plan-r1' and x['RW'] for x in app['Mounts'])
assert json.loads(wsl('docker','network','inspect','m09s07-plan-r1-net'))[0]['Internal']
g=R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md';gb=g.read_bytes()
note=(O/'status-note.md').read_bytes().replace(b'\r\n',b'\n').rstrip(b'\n')+b'\n\n'
assert gb.count(note)==1 and hashlib.sha256(gb.replace(note,b'',1)).hexdigest()==e['guide_sha256']
for p in O.glob('*.md'):
 text=p.read_text(encoding='utf-8');assert not any(l.endswith((' ','\t')) for l in text.splitlines()),p.name
 for link in re.findall(r'\]\(([^)]+)\)',text):
  if '://' in link or link.startswith('#'):continue
  root=g.parent if p.name=='status-note.md' else O;path=link.split('#')[0]
  assert (root/path).exists() or path in ['artifact-manifest.json','preservation.json'],(p.name,link)
for p in O.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=p.name)
assert not any(p.name in {'.env','runtime.py','qa_settings.py'} for p in O.rglob('*'))
check=subprocess.run(['git','diff','--check','--',str(g)],cwd=R,capture_output=True,text=True);assert check.returncode==0
(O/'containers-final.txt').write_text(containers)
preserve={'sources1021_unchanged':True,'application_changes':0,'head':e['head'],'branch':e['branch'],'index_tree':e['index_tree'],
 'task33_ref':e['task33_ref'],'staged_diff_empty':True,'active_run':active,'sharedMO_match':True,'cbmignore_match':True,
 'prior_manifest_counts':oldcounts,'prior_verification_hashes_match':True,'entry_container_ids_states_match':38,'new_own_containers':2,
 'foreign_restarts':0,'whole_machine_process_continuity':'NOT VERIFIED; bounded Docker snapshot',
 'guide_old_bytes_preserved':True,'guide_after_sha256':sha(g)}
(O/'preservation.json').write_text(json.dumps(preserve,indent=2)+'\n')
manifest={p.relative_to(O).as_posix():sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ['artifact-manifest.json','verification.json']}
(O/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
assert all(sha(O/path)==h for path,h in load(O/'artifact-manifest.json').items())
v=load(O/'verification.json');v.update(metadata_gate='PASS: integrity only; SOCIAL07 OPEN/P3, approvalPENDING',
 final_verifier_exit=0,final_utc=datetime.now(timezone.utc).isoformat(),preservation=preserve,
 artifact_manifest={'files':len(manifest),'sha256':sha(O/'artifact-manifest.json'),'excludes':['artifact-manifest.json','verification.json']})
(O/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'decision':v['decision'],'app_changes':0,'source_files':1021,'native':'66cells540controlPASS144sourceFAIL',
 'candidate_baseline':'9unique/7failed2PASS/18assertionFAIL/0errors','PNG':114,'entry_containers_preserved':38,
 'prior_packages':8,'artifacts':len(manifest),'metadata_gate':'PASS','UTC':v['final_utc']}))
