"""Final bounded source/evidence gate; does not turn retained shared FAIL into PASS."""
import ast
from collections import Counter
from datetime import datetime,timezone
import hashlib,itertools,json,re,struct,subprocess
from pathlib import Path
from urllib.request import urlopen

O=Path(__file__).resolve().parent;R=O.parents[2];Q=R/'.tmp/social05-pc-fix-r1'
P=R/'docs/qa/social-qa05-recheck-2026-10-17-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True,encoding='utf-8').rstrip('\r\n')
def wsl(*args):return subprocess.check_output(['wsl','-d','Ubuntu-24.04','--',*args],text=True)
e=load(O/'entry.json');green=load(O/'source-final.json')['sources']
assert len(e['sources'])==len(green)==1021
assert all(sha(R/p)==h for p,h in green.items())
assert [p for p,h in e['sources'].items() if green[p]!=h]==['static/css/site.css']
assert git('rev-parse','HEAD')==e['head']=='852938d96764ae315b92859e3651e5ea62054a36'
assert git('branch','--show-current')==e['branch']=='codex/module09-transfer-2026-10-16-r1'
assert git('rev-parse','task33-progress')==e['task33_ref']
assert git('rev-parse','HEAD^{tree}')==e['index_tree']
assert not git('diff','--cached','--name-only')
active=[s for s in (R/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if s.startswith('active_run:')]
assert active==e['active_run']==['active_run: NONE']
assert all(sha(R/p)==h for p,h in e['shared_mo'].items())
assert sha(R/'.cbmignore')==e['cbmignore_sha256']
currentpaths={l[3:] for l in git('status','--porcelain=v1','-uall').splitlines()}
oldpaths={l[3:] for l in e['status'].splitlines()}
assert oldpaths<=currentpaths
assert all(p in oldpaths or p.startswith(O.relative_to(R).as_posix()+'/') for p in currentpaths)
candidate=load(P/'candidate-manifest.json')
normalized=(R/'static/css/site.css').read_text(encoding='utf-8')
assert hashlib.sha256(normalized.encode()).hexdigest()==candidate['after_normalized_sha256']
rules=(P/'candidate-rules.css').read_text()
assert normalized.count(rules+'\n')==1
assert hashlib.sha256(normalized.replace(rules+'\n','',1).encode()).hexdigest()==candidate['before_normalized_sha256']
assert sha(O/'applied.diff')==sha(P/'proposed.diff')==load(O/'approval.json')['candidate_sha256']
assert load(O/'approval.json')['scope']==['static/css/site.css']
assert all(sha(P/p)==h for p,h in e['prior_plan_files'].items()) and len(e['prior_plan_files'])==81
oldcounts={}
for n,expected in [('module09-pc-resume-2026-10-16-r1',43),('social-qa03-fix-2026-10-16-pc-r1',181),
 ('social-qa04-recheck-2026-10-16-pc-r1',149),('social-qa04-fix-2026-10-17-pc-r1',212)]:
 d=load(O.parent/n/'artifact-manifest.json')
 assert len(d)==expected and all(sha(O.parent/n/p)==h for p,h in d.items()),n
 oldcounts[n]=expected

m=load(O/'matrix.json');b=load(O/'boundary.json')
assert len(m)==36 and {(r['item']['role'],r['item']['lang'],r['item']['width']) for r in m}==set(itertools.product(
 ['author','guest'],['ru','az','en'],[360,390,768,1024,1280,1440]))
assert sum(sum(r['controls'].values()) for r in m)==324
assert sum(sum(r['layout'].values()) for r in m)==234
assert all(all(r['controls'].values()) and all(r['layout'].values()) for r in m)
assert len(b)==6 and {(r['item']['lang'],r['item']['width']) for r in b}==set(itertools.product(['ru','az','en'],[760,761]))
assert sum(sum(r['controls'].values()) for r in b)==sum(sum(r['layout'].values()) for r in b)==54
assert all(all(r['controls'].values()) and all(r['layout'].values()) for r in b)
assert all(r['before']==r['after'] for r in m+b)
assert all(not r[k] for r in m+b for k in ['pageerrors','request_failed','http_failures'])
assert all(r['facts']['documentWidth']==r['item']['width'] for r in m+b)
a=load(O/'actions.json');t=load(O/'submit_transport.json');s=load(O/'shared.json');base=load(O/'shared_baseline.json')
assert len(a['rows'])==17 and sum(sum(r['checks'].values()) for r in a['rows'])==147
assert len(t['rows'])==1 and sum(sum(r['checks'].values()) for r in t['rows'])==8
assert all(all(r['checks'].values()) for d in [a,t] for r in d['rows'])
assert not any(d.get('fatal') or d.get('pageerrors') for d in [a,t,s,base])
assert len(a['request_failed'])==len(t['request_failed'])==1
assert len(s['rows'])==36
assert {(r['kind'],r['lang'],r['width']) for r in s['rows']}==set(itertools.product(
 ['place','activity','specialist','event'],['ru','az','en'],[390,768,1440]))
assert sum(sum(r['checks'].values()) for r in s['rows'])==243
fail=[r for r in s['rows'] if not all(r['checks'].values())]
assert len(fail)==9 and all(r['kind']=='activity' and [k for k,v in r['checks'].items() if not v]==['target_heading'] for r in fail)
assert not s['http_failures']
assert len(base['rows'])==9 and sum(sum(r['checks'].values()) for r in base['rows'])==36
assert all(all(r['checks'].values()) for r in base['rows'])
assert {(r['lang'],r['width']) for r in fail}=={(r['lang'],r['width']) for r in base['rows']}
for r in fail:
 match=next(v for v in base['rows'] if (v['lang'],v['width'])==(r['lang'],r['width']))
 assert r['facts']['heading'].strip()==match['facts']['heading']
 assert match['facts']['baseline_css_sha256']==candidate['before_normalized_sha256']
assert load(O/'red-reference.json')['matrix_sha256']==sha(P/'matrix.json')
red=load(P/'matrix.json')
assert sum(sum(not v for v in r['layout'].values()) for r in red)==24
assert sum(sum(not v for v in r['layout'].values()) for r in m)==0

log=(O/'baseline.log').read_text()
assert (O/'baseline.exit').read_text().strip()=='0' and 'Ran 3 tests in 0.355s' in log and '\nOK\n' in log
ids=re.findall(r'\((catalog\.testcases\.public\.TestReviewEnhancements\.[^)]+)\) \.\.\.',log)
assert len(ids)==len(set(ids))==3 and not re.search(r'^FAIL:|^ERROR:',log,re.M)
pngs=load(O/'png-manifest.json')
assert len(pngs)==111 and len({p['path'] for p in pngs})==111
assert Counter(p['kind'] for p in pngs)=={'actual-patched-source':98,'SIMULATED-transport-or-baseline':13}
assert {p.relative_to(O).as_posix() for p in (O/'screenshots').glob('*.png')}=={p['path'] for p in pngs}
for p in pngs:
 raw=(O/p['path']).read_bytes()
 assert sha(O/p['path'])==p['sha256'] and raw[:8]==b'\x89PNG\r\n\x1a\n' and p['native']
 assert struct.unpack('>II',raw[16:24])==(p['width'],p['height'])
assert all((O/r['png']).is_file() for r in m+b+s['rows']+base['rows'])
assert all((O/p).is_file() for p in a['pngs'])

runtime=load(O/'runtime-info.json');live=load(O/'live-final.json')
assert live==runtime and live['testing'] and live['source_files']==1021
assert live['sole_locales']==['/mnt/c/kidsmap/.tmp/social05-pc-fix-r1/locales/locale']
assert all(green[p]==h for p,h in live['hashes'].items())
with urlopen('http://127.0.0.1:33326/qa/info/',timeout=10) as response:assert json.load(response)==live
with urlopen('http://127.0.0.1:33326/static/css/site.css',timeout=10) as response:
 assert response.status==200 and hashlib.sha256(response.read()).hexdigest()==green['static/css/site.css']
assert load(O/'static-proof.json')['sha256']==green['static/css/site.css']
locales=load(O/'locale-manifest.json')
assert locales['status']=='complete' and set(locales['locales'])=={'ru','az','en'}
for r in locales['entries']:
 assert sha(R/'locale'/r['source'])==r['po_sha256']
 assert sha(Q/'locales'/r['snapshot'])==r['po_sha256']
 assert sha(Q/'locales'/r['mo'])==r['mo_sha256'] and r['exit_code']==0
with urlopen('http://127.0.0.1:33326/qa/state/',timeout=10) as response:state=json.load(response)
assert state==load(O/'aggregate-final.json')
assert state['reviews']==3 and state['approved']==2 and state['pending']==state['author_pending']==state['reactions']==1
assert state['author_rating4']==state['author_name80']==1

containers=wsl('docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}} {{.Ports}}')
byname=lambda v:{l.split()[1]:l.split()[:3] for l in v.splitlines() if l.strip()}
old,current=byname((O/'containers-entry.txt').read_text()),byname(containers)
assert len(old)==34 and all(current.get(k)==v for k,v in old.items())
assert set(current)-set(old)=={'m09s05-fix-r1-app'} and current['m09s05-fix-r1-app'][2]=='running'
info=json.loads(wsl('docker','inspect','m09s05-fix-r1-app'))[0]
assert info['HostConfig']['ReadonlyRootfs'] and info['Config']['Labels']['codex.owner']=='social05-pc-fix-r1'
assert set(info['NetworkSettings']['Networks'])=={'m09s05-plan-r1-net'}
assert any(m['Destination']=='/mnt/c/kidsmap' and not m['RW'] for m in info['Mounts'])
assert any(m['Destination']=='/mnt/c/kidsmap/.tmp/social05-pc-fix-r1' and m['RW'] for m in info['Mounts'])
assert json.loads(wsl('docker','network','inspect','m09s05-plan-r1-net'))[0]['Internal']

guide=R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md'
note=(O/'status-note.md').read_bytes().replace(b'\r\n',b'\n').rstrip(b'\n')+b'\n\n'
gb=guide.read_bytes();assert gb.count(note)==1
assert hashlib.sha256(gb.replace(note,b'',1)).hexdigest()==e['guide_sha256']
for p in O.glob('*.md'):
 text=p.read_text(encoding='utf-8')
 assert not any(l.endswith((' ','\t')) for l in text.splitlines()),p.name
 for link in re.findall(r'\]\(([^)]+)\)',text):
  if '://' in link or link.startswith('#'):continue
  relative=link.split('#')[0]
  root=guide.parent if p.name=='status-note.md' else O
  assert (root/relative).exists() or relative in ['artifact-manifest.json','preservation.json'],(p.name,link)
for p in O.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=p.name)
assert not any(p.name in {'.env','qa_settings.py','runtime.py'} for p in O.rglob('*'))
check=subprocess.run(['git','diff','--check','--','static/css/site.css',str(guide)],cwd=R,capture_output=True,text=True)
assert check.returncode==0,check.stdout+check.stderr
(O/'containers-final.txt').write_text(containers)
preserve={'source_files':1021,'application_changed':['static/css/site.css'],'other1020_bytes_match':True,
 'head':e['head'],'branch':e['branch'],'index_tree':e['index_tree'],'staged_diff_empty':True,
 'task33_ref':e['task33_ref'],'active_run':active,'shared_mo_match':True,'cbmignore_match':True,
 'prior_plan_files':81,'old_artifact_manifests':oldcounts,'entry_containers_ids_states_match':34,
 'new_own_containers':1,'foreign_restart_commands':0,'own_serve_helper_reload':1,
 'whole_machine_process_continuity':'NOT VERIFIED; bounded Docker snapshot',
 'guide_old_bytes_preserved':True,'guide_after_sha256':sha(guide)}
(O/'preservation.json').write_text(json.dumps(preserve,indent=2)+'\n')
manifest={p.relative_to(O).as_posix():sha(p) for p in sorted(O.rglob('*')) if p.is_file()
 and p.name not in {'artifact-manifest.json','verification.json'}}
(O/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
assert all(sha(O/p)==h for p,h in load(O/'artifact-manifest.json').items())
v=load(O/'verification.json')
v.update(metadata_gate='PASS: source/evidence/preservation;9unrelated headingFAIL retained',
 final_verifier_exit=0,final_utc=datetime.now(timezone.utc).isoformat(),preservation=preserve,
 backend_method_ids=ids,artifact_manifest={'files':len(manifest),'sha256':sha(O/'artifact-manifest.json'),
 'excludes':['verification.json','artifact-manifest.json']})
(O/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'decision':v['decision'],'metadata_gate':v['metadata_gate'],'app_files':1,
 'matrix_layout':'234PASS/0FAIL','boundary':'108PASS','actions_and_transport':'155PASS',
 'shared':'243PASS/9existingFAIL;36originalCSSparityPASS','backend':'3uniquePASS0F/0E',
 'PNG':111,'prior_plan_files_preserved':81,'entry_containers_preserved':34,'artifacts':len(manifest),'UTC':v['final_utc']}))
