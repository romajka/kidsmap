"""PLAN06 integrity gate; a passing metadata gate leaves the finding OPEN."""
import ast
from datetime import datetime,timezone
import hashlib,itertools,json,re,struct,subprocess
from pathlib import Path
from urllib.request import urlopen
O=Path(__file__).resolve().parent;R=O.parents[2];Q=R/'.tmp/social06-pc-plan-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True,encoding='utf-8').rstrip('\r\n')
def wsl(*args):return subprocess.check_output(['wsl','-d','Ubuntu-24.04','--',*args],text=True)
e=load(O/'source-entry.json')
assert len(e['sources'])==1021 and all(sha(R/p)==h for p,h in e['sources'].items())
assert load(O/'source-final.json')['sources']==e['sources']
assert all(sha(R/p)==h for p,h in e['shared_mo'].items())
assert sha(R/'.cbmignore')==e['cbmignore_sha256']
assert git('rev-parse','HEAD')==e['head']=='852938d96764ae315b92859e3651e5ea62054a36'
assert git('branch','--show-current')==e['branch']=='codex/module09-transfer-2026-10-16-r1'
assert git('rev-parse','HEAD^{tree}')==e['index_tree'] and git('rev-parse','task33-progress')==e['task33_ref']
assert not git('diff','--cached','--name-only')
active=[l for l in (R/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if l.startswith('active_run:')]
assert active==e['active_run']==['active_run: NONE']
oldpaths={l[3:] for l in e['status'].splitlines()}
newpaths={l[3:] for l in git('status','--porcelain=v1','-uall').splitlines()}
assert oldpaths<=newpaths and all(p in oldpaths or p.startswith(O.relative_to(R).as_posix()+'/') for p in newpaths)
guide=R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md';gb=guide.read_bytes()
note=(O/'status-note.md').read_bytes().replace(b'\r\n',b'\n').rstrip(b'\n')+b'\n\n'
assert gb.count(note)==1 and hashlib.sha256(gb.replace(note,b'',1)).hexdigest()==e['guide_sha256']
counts={}
for name,fingerprints in e['prior_packages'].items():
 p=O.parent/name
 assert sha(p/'artifact-manifest.json')==fingerprints['manifest_sha256']
 assert sha(p/'verification.json')==fingerprints['verification_sha256']
 m=load(p/'artifact-manifest.json');assert all(sha(p/path)==h for path,h in m.items()),name
 counts[name]=len(m)
assert len(counts)==6

matrix=load(O/'matrix.json')
assert len(matrix)==18 and {(r['item']['lang'],r['item']['width']) for r in matrix}==set(itertools.product(['ru','az','en'],[360,390,768,1024,1280,1440]))
assert sum(sum(r['controls'].values()) for r in matrix)==198
assert all(len(r['controls'])==11 and all(r['controls'].values()) for r in matrix)
assert sum(sum(not v for v in r['source'].values()) for r in matrix)==144
assert all(len(r['source'])==8 and not any(r['source'].values()) for r in matrix)
assert all(not r[k] for r in matrix for k in ['pageerrors','http_failures','request_failed'])
assert all(r['before']==r['after'] for r in matrix)
for r in matrix:
 f=r['facts']
 assert f['initial']['rating']=='5'
 assert all(f[k]['rating']=='3' and f[k]['active']==['1','2','3'] for k in ['space','enter'])
 assert all(f[k]['roles']==[None]*5 and f[k]['checked']==[None]*5 for k in ['initial','space','enter'])
 assert f['space']['tabIndices']==[0]*5 and f['shiftBack']['focused']=='5'
 assert f['arrow']['rating']=='3' and f['arrow']['focused']=='3'
 assert 'button "3"' in f['spaceAX'] and '[checked]' not in f['spaceAX']
 assert all((O/p).is_file() for p in r['pngs'])
pngs=load(O/'png-manifest.json')
assert len(pngs)==36 and len({p['path'] for p in pngs})==36
assert {p.relative_to(O).as_posix() for p in (O/'screenshots').glob('*.png')}=={p['path'] for p in pngs}
for p in pngs:
 raw=(O/p['path']).read_bytes()
 assert sha(O/p['path'])==p['sha256'] and raw[:8]==b'\x89PNG\r\n\x1a\n' and p['native']
 assert struct.unpack('>II',raw[16:24])==(p['width'],p['height'])
c=load(O/'candidate-manifest.json');assert c['scope']==['src/catalog/templates/pages/site_reviews.html'] and not c['applied']
before=(R/c['scope'][0]).read_text(encoding='utf-8')
assert hashlib.sha256(before.encode()).hexdigest()==c['before_normalized_sha256']
assert sha(O/'candidate-site_reviews.html')==c['candidate_sha256']==c['after_normalized_sha256']
assert sha(O/'proposed.diff')==c['diff_sha256']
check=subprocess.run(['git','apply','--check','--ignore-space-change',str(O/'proposed.diff')],cwd=R,capture_output=True,text=True)
assert check.returncode==0,check.stderr
for js in ['candidate-inline.js','acceptance-extra.js']:
 result=subprocess.run(['wsl','-d','Ubuntu-24.04','--','node','--check',str(Q/js).replace('C:\\','/mnt/c/').replace('\\','/')],capture_output=True,text=True)
 assert result.returncode==0,result.stderr

info=load(O/'runtime-info.json');assert info==load(O/'live-final.json')
assert info['testing'] and info['source_files']==1021
assert info['sole_locales']==['/mnt/c/kidsmap/.tmp/social06-pc-plan-r1/locales/locale']
assert all(e['sources'][p]==h for p,h in info['hashes'].items())
with urlopen('http://127.0.0.1:33336/qa/info/',timeout=10) as response:assert json.load(response)==info
with urlopen('http://127.0.0.1:33336/static/css/site.css',timeout=10) as response:assert hashlib.sha256(response.read()).hexdigest()==e['sources']['static/css/site.css']
locales=load(O/'locale-manifest.json')
assert locales['status']=='complete' and set(locales['locales'])=={'ru','az','en'}
for r in locales['entries']:
 assert sha(R/'locale'/r['source'])==r['po_sha256']==sha(Q/'locales'/r['snapshot'])
 assert sha(Q/'locales'/r['mo'])==r['mo_sha256'] and r['exit_code']==0
containers=wsl('docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}} {{.Ports}}')
byname=lambda text:{l.split()[1]:l.split()[:3] for l in text.splitlines() if l.strip()}
old,current=byname((O/'containers-entry.txt').read_text()),byname(containers)
assert len(old)==35 and all(current.get(n)==v for n,v in old.items())
assert set(current)-set(old)=={'m09s06-plan-r1-app','m09s06-plan-r1-pg'}
app=json.loads(wsl('docker','inspect','m09s06-plan-r1-app'))[0]
assert app['State']['Running'] and app['HostConfig']['ReadonlyRootfs']
assert app['Config']['Labels']['codex.owner']=='social06-pc-plan-r1'
assert set(app['NetworkSettings']['Networks'])=={'m09s06-plan-r1-net'}
assert any(m['Destination']=='/mnt/c/kidsmap' and not m['RW'] for m in app['Mounts'])
assert any(m['Destination']=='/mnt/c/kidsmap/.tmp/social06-pc-plan-r1' and m['RW'] for m in app['Mounts'])
assert json.loads(wsl('docker','network','inspect','m09s06-plan-r1-net'))[0]['Internal']
for p in O.glob('*.md'):
 text=p.read_text(encoding='utf-8');assert not any(l.endswith((' ','\t')) for l in text.splitlines()),p.name
 for link in re.findall(r'\]\(([^)]+)\)',text):
  if '://' in link or link.startswith('#'):continue
  root=guide.parent if p.name=='status-note.md' else O
  path=link.split('#')[0]
  assert (root/path).exists() or path in ['artifact-manifest.json','preservation.json'],(p.name,link)
for p in O.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=p.name)
assert not any(p.name in {'.env','qa_settings.py','runtime.py'} for p in O.rglob('*'))
(O/'containers-final.txt').write_text(containers)
preserve={'sources1021_unchanged':True,'application_changes':0,'head':e['head'],'branch':e['branch'],
 'index_tree':e['index_tree'],'task33_ref':e['task33_ref'],'staged_diff_empty':True,'active_run':active,
 'shared_mo_match':True,'cbmignore_match':True,'prior_packages_manifest_counts':counts,'prior_verification_hashes_match':True,
 'entry_container_ids_states_match':35,'new_own_containers':2,'foreign_restart_commands':0,
 'whole_machine_process_continuity':'NOT VERIFIED; bounded Docker snapshot','guide_old_bytes_preserved':True,'guide_after_sha256':sha(guide)}
(O/'preservation.json').write_text(json.dumps(preserve,indent=2)+'\n')
manifest={p.relative_to(O).as_posix():sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ['artifact-manifest.json','verification.json']}
(O/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
assert all(sha(O/p)==h for p,h in load(O/'artifact-manifest.json').items())
v=load(O/'verification.json');v.update(metadata_gate='PASS: source/evidence integrity only;06OPEN and approvalPENDING',
 final_verifier_exit=0,final_utc=datetime.now(timezone.utc).isoformat(),preservation=preserve,
 artifact_manifest={'files':len(manifest),'sha256':sha(O/'artifact-manifest.json'),'excludes':['artifact-manifest.json','verification.json']})
(O/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'decision':v['decision'],'application_changes':0,'source_files':1021,'native':'18cells198controlPASS144sourceFAIL',
 'PNG':36,'foreign_entry_containers_preserved':35,'prior_packages':6,'artifacts':len(manifest),'metadata_gate':'PASS','UTC':v['final_utc']}))
