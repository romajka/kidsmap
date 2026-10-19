"""Bounded06 final evidence/source gate. Retains initial reset FAIL as history."""
import ast,difflib,hashlib,itertools,json,re,struct,subprocess
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlparse
O=Path(__file__).resolve().parent;R=O.parents[2];Q=R/'.tmp/social06-pc-fix-r1'
P=R/'docs/qa/social-qa06-recheck-2026-10-17-pc-r1';target='src/catalog/templates/pages/site_reviews.html'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True,encoding='utf-8').rstrip('\r\n')
def wsl(*args):return subprocess.check_output(['wsl','-d','Ubuntu-24.04','--',*args],text=True)
e=load(O/'entry.json');final=load(O/'source-final.json')['sources'];initial=load(O/'initial-source.json')['sources']
assert len(e['sources'])==len(final)==1021
assert all(sha(R/p)==h for p,h in final.items())
assert [p for p,h in e['sources'].items() if final[p]!=h]==[target]
assert [p for p,h in e['sources'].items() if initial[p]!=h]==[target]
assert final==load(O/'green-source.json')['sources']
assert git('rev-parse','HEAD')==e['head']=='852938d96764ae315b92859e3651e5ea62054a36'
assert git('branch','--show-current')==e['branch']=='codex/module09-transfer-2026-10-16-r1'
assert git('rev-parse','HEAD^{tree}')==e['index_tree'] and git('rev-parse','task33-progress')==e['task33_ref']
assert not git('diff','--cached','--name-only')
active=[l for l in (R/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if l.startswith('active_run:')]
assert active==e['active_run']==['active_run: NONE']
assert all(sha(R/p)==h for p,h in e['shared_mo'].items()) and sha(R/'.cbmignore')==e['cbmignore_sha256']
oldpaths={l[3:] for l in e['status'].splitlines()};currentpaths={l[3:] for l in git('status','--porcelain=v1','-uall').splitlines()}
assert oldpaths<=currentpaths
assert all(p in oldpaths or p==target or p.startswith(O.relative_to(R).as_posix()+'/') for p in currentpaths)
assert len(e['prior_plan_files'])==70 and all(sha(P/p)==h for p,h in e['prior_plan_files'].items())
oldcounts={}
for name,fingerprints in e['prior_packages'].items():
 p=O.parent/name
 assert sha(p/'artifact-manifest.json')==fingerprints['manifest_sha256']
 assert sha(p/'verification.json')==fingerprints['verification_sha256']
 manifest=load(p/'artifact-manifest.json');assert all(sha(p/path)==h for path,h in manifest.items()),name
 oldcounts[name]=len(manifest)
assert len(oldcounts)==6
approval=load(O/'approval.json');assert approval['scope']==[target] and approval['human_message']=='одобряю'
assert approval['diff_sha256']==sha(P/'proposed.diff')==sha(O/'initial-applied.diff')
candidate=load(P/'candidate-manifest.json')
norm=(R/target).read_text(encoding='utf-8')
without_reset_iteration=norm.replace('        const defaultRating = Number(input.defaultValue || 5);\n','').replace(
 'choose(defaultRating);','choose(Number(input.value || 5));')
assert without_reset_iteration==(P/'candidate-site_reviews.html').read_text(encoding='utf-8')
assert hashlib.sha256(without_reset_iteration.encode()).hexdigest()==candidate['after_normalized_sha256']
before=subprocess.check_output(['git','show','HEAD:'+target],cwd=R,text=True,encoding='utf-8')
assert hashlib.sha256(before.encode()).hexdigest()==candidate['before_normalized_sha256']
expected_diff=''.join(difflib.unified_diff(before.splitlines(keepends=True),norm.splitlines(keepends=True),fromfile='a/'+target,tofile='b/'+target))
assert (O/'applied.diff').read_text(encoding='utf-8')==expected_diff
assert load(O/'reset-iteration.json')['final_template_sha256']==final[target]

m=load(O/'matrix.json')
assert len(m)==18 and {(r['item']['lang'],r['item']['width']) for r in m}==set(itertools.product(['ru','az','en'],[360,390,768,1024,1280,1440]))
assert sum(sum(r['controls'].values()) for r in m)==198
assert sum(sum(r['source'].values()) for r in m)==144
assert all(all(r['controls'].values()) and all(r['source'].values()) for r in m)
assert all(not r[k] for r in m for k in ['pageerrors','http_failures','request_failed'])
assert all(r['before']==r['after'] for r in m)
assert all('radio "3 / 5" [checked]' in r['facts']['spaceAX'] and 'radio "3 / 5" [checked]' in r['facts']['enterAX'] for r in m)
extended=load(O/'initial-acceptance-extra.json')
assert len(extended['rows'])==9 and sum(sum(r['checks'].values()) for r in extended['rows'])==117
assert all([k for k,v in r['checks'].items() if not v]==['reset5'] for r in extended['rows'])
assert not extended.get('pageerrors')
assert load(O/'acceptance-extra.json')==extended
reset=load(O/'reset-recheck.json')
assert len(reset['rows'])==9 and sum(sum(r['checks'].values()) for r in reset['rows'])==27
assert all(all(r['checks'].values()) for r in reset['rows']) and not reset.get('pageerrors')
assert {(r['lang'],r['width']) for r in extended['rows']}=={(r['lang'],r['width']) for r in reset['rows']}
for r in reset['rows']:
 assert r['facts']['chosen']['rating']==r['facts']['chosen']['defaultValue']==2
 assert r['facts']['reset']['rating']==r['facts']['reset']['defaultValue']==5
 assert r['facts']['reset']['checked']==r['facts']['reset']['tab']==[5]
a=load(O/'actions.json')
assert len(a['rows'])==9 and sum(sum(r['checks'].values()) for r in a['rows'])==68
assert all(all(r['checks'].values()) for r in a['rows']) and not a.get('fatal') and not a['pageerrors']
assert len(a['request_failed'])==1 and '/en/review/' in a['request_failed'][0]['url']
assert [r['facts']['rating'] for r in a['rows'] if r['id'].startswith('native-submit-')]==[3,1,5]
assert all(r['facts']['after']['own_pending_rating']==r['facts']['rating'] for r in a['rows'] if r['id'].startswith('native-submit-'))
s=load(O/'shared.json')
assert len(s['rows'])==45 and sum(sum(r['checks'].values()) for r in s['rows'])==270
assert all(all(r['checks'].values()) for r in s['rows']) and not s.get('fatal') and not s['pageerrors']
assert s['before']==s['after']
assert {(r['kind'],r['lang'],r['width']) for r in s['rows']}==set(itertools.product(
 ['home','place_detail','activity','specialist','event'],['ru','az','en'],[390,768,1440]))
assert sum(r['facts'].get('existing_social07',False) for r in s['rows'])==9
assert len(s['http_failures'])==81 and len({r['url'] for r in s['http_failures']})==9
assert all(r['status']==404 and urlparse(r['url']).path.startswith('/media/site/gallery/') for r in s['http_failures'])
assert len(s['request_failed'])==36
assert all(urlparse(r['url']).hostname in ['unpkg.com','maps.google.com'] for r in s['request_failed'])
red=load(P/'matrix.json');assert sum(sum(not v for v in r['source'].values()) for r in red)==144
assert load(O/'red-reference.json')['matrix_sha256']==sha(P/'matrix.json')

pngs=load(O/'png-manifest.json')
assert len(pngs)==107 and len({p['path'] for p in pngs})==107
assert Counter(p['kind'] for p in pngs)=={'retained-reset-failure':9,'SIMULATED-transport':2,'accepted-initial-nonreset':36,'final-source':60}
assert {p.relative_to(O).as_posix() for p in (O/'screenshots').glob('*.png')}=={p['path'] for p in pngs}
for p in pngs:
 raw=(O/p['path']).read_bytes();assert sha(O/p['path'])==p['sha256'] and raw[:8]==b'\x89PNG\r\n\x1a\n' and p['native']
 assert struct.unpack('>II',raw[16:24])==(p['width'],p['height'])
for row in m:
 assert all((O/p).is_file() for p in row['pngs'])
for row in extended['rows']+reset['rows']+s['rows']:
 assert (O/row['png']).is_file()
assert all((O/p).is_file() for p in a['pngs'])
originalinfo=load(O/'runtime-info.json');info=load(O/'runtime-info-final.json')
assert originalinfo['hashes'][target]==initial[target]
assert info==load(O/'live-final.json') and info['hashes'][target]==final[target]
assert info['testing'] and info['source_files']==1021 and info['sole_locales']==['/mnt/c/kidsmap/.tmp/social06-pc-fix-r1/locales/locale']
with urlopen('http://127.0.0.1:33337/qa/info/',timeout=10) as response:assert json.load(response)==info
with urlopen('http://127.0.0.1:33337/qa/state/',timeout=10) as response:state=json.load(response)
assert state==load(O/'aggregate-final.json')
assert state['reviews']==5 and state['approved']==2 and state['pending']==3 and state['case_pending_ratings']==[1,3,5] and state['reactions']==0
loc=load(O/'locale-manifest.json');assert loc['status']=='complete' and set(loc['locales'])=={'ru','az','en'}
for r in loc['entries']:
 assert sha(R/'locale'/r['source'])==r['po_sha256']==sha(Q/'locales'/r['snapshot'])
 assert sha(Q/'locales'/r['mo'])==r['mo_sha256'] and r['exit_code']==0
containers=wsl('docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}} {{.Ports}}')
byname=lambda text:{l.split()[1]:l.split()[:3] for l in text.splitlines() if l.strip()}
old,current=byname((O/'containers-entry.txt').read_text()),byname(containers)
assert len(old)==37 and all(current.get(n)==v for n,v in old.items())
assert set(current)-set(old)=={'m09s06-fix-r1-app'} and current['m09s06-fix-r1-app'][2]=='running'
app=json.loads(wsl('docker','inspect','m09s06-fix-r1-app'))[0]
assert app['HostConfig']['ReadonlyRootfs'] and app['Config']['Labels']['codex.owner']=='social06-pc-fix-r1'
assert set(app['NetworkSettings']['Networks'])=={'m09s06-plan-r1-net'}
assert any(mount['Destination']=='/mnt/c/kidsmap' and not mount['RW'] for mount in app['Mounts'])
assert any(mount['Destination']=='/mnt/c/kidsmap/.tmp/social06-pc-fix-r1' and mount['RW'] for mount in app['Mounts'])
assert json.loads(wsl('docker','network','inspect','m09s06-plan-r1-net'))[0]['Internal']
assert json.loads(wsl('docker','inspect','m09s06-plan-r1-pg'))[0]['Id']==load(O/'ownership.json')['verified_own_pg_id']
g=R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md';gb=g.read_bytes()
note=(O/'status-note.md').read_bytes().replace(b'\r\n',b'\n').rstrip(b'\n')+b'\n\n'
assert gb.count(note)==1 and hashlib.sha256(gb.replace(note,b'',1)).hexdigest()==e['guide_sha256']
for p in O.glob('*.md'):
 text=p.read_text(encoding='utf-8');assert not any(line.endswith((' ','\t')) for line in text.splitlines()),p.name
 for link in re.findall(r'\]\(([^)]+)\)',text):
  if '://' in link or link.startswith('#'):continue
  root=g.parent if p.name=='status-note.md' else O;path=link.split('#')[0]
  assert (root/path).exists() or path in ['artifact-manifest.json','preservation.json'],(p.name,link)
for p in O.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=p.name)
assert not any(p.name in {'.env','runtime.py','qa_settings.py'} for p in O.rglob('*'))
check=subprocess.run(['git','diff','--check','--',target,str(g)],cwd=R,capture_output=True,text=True)
assert check.returncode==0,check.stdout+check.stderr
(O/'containers-final.txt').write_text(containers)
preserve={'sources':1021,'application_changed':[target],'other1020_bytes_match':True,'head':e['head'],'branch':e['branch'],
 'index_tree':e['index_tree'],'task33_ref':e['task33_ref'],'staged_diff_empty':True,'active_run':active,
 'shared_mo_match':True,'cbmignore_match':True,'prior_plan_files_preserved':70,'old_manifest_counts':oldcounts,
 'entry_container_ids_states_match':37,'new_own_containers':1,'foreign_restarts':0,'own_serve_reload':1,
 'whole_machine_process_continuity':'NOT VERIFIED; bounded Docker snapshot','guide_old_bytes_preserved':True,'guide_after_sha256':sha(g)}
(O/'preservation.json').write_text(json.dumps(preserve,indent=2)+'\n')
manifest={p.relative_to(O).as_posix():sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ['artifact-manifest.json','verification.json']}
(O/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
assert all(sha(O/path)==h for path,h in load(O/'artifact-manifest.json').items())
v=load(O/'verification.json');v.update(metadata_gate='PASS: source/evidence/preservation; initial reset FAIL and media limitations retained',
 final_verifier_exit=0,final_utc=datetime.now(timezone.utc).isoformat(),preservation=preserve,
 artifact_manifest={'files':len(manifest),'sha256':sha(O/'artifact-manifest.json'),'excludes':['artifact-manifest.json','verification.json']})
(O/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'decision':v['decision'],'app_files':1,'matrix':'18cells198+144PASS retained initial source',
 'extended':'117PASS/9initialFAIL retained; final targeted27PASS','actions':'68PASS','shared':'270boundedPASS/45cells; network limitations retained',
 'PNG':107,'entry_containers_preserved':37,'prior_plan_files':70,'artifacts':len(manifest),'metadata_gate':'PASS','UTC':v['final_utc']}))
