"""Final audit-only evidence/integrity; update exactly journal row02."""
from pathlib import Path
import hashlib,json,subprocess,re,datetime,sys,urllib.request
sys.stdout.reconfigure(encoding='utf-8')
h=Path(__file__).resolve().parent;root=h.parents[2];state=root/'.tmp/module02-20261009-r1'
s=json.loads((h/'snapshot.json').read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changes=[p for p,digest in s['source_files'].items() if not (root/p).exists() or sha(root/p)!=digest]
prior=[p for p,digest in s['preserved_module01'].items() if not (root/p).exists() or sha(root/p)!=digest]
assert not changes,changes;assert not prior,prior
currentfiles={p.relative_to(root).as_posix() for top in ['src','static','config','locale'] for p in (root/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
assert currentfiles==set(s['source_files']),list(currentfiles-set(s['source_files']))
assert sha(root/'docs/task33/implementation-status.md')==s['entry_active_marker_sha256']
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip();assert head==s['head']
journal=h.parent/'module-acceptance-prompts.md';entry=state/'journal-before.bin'
if not entry.exists():
 assert sha(journal)==s['entry_journal_sha256'];entry.write_bytes(journal.read_bytes())
before=entry.read_bytes();assert hashlib.sha256(before).hexdigest()==s['entry_journal_sha256']
row='| 02 | Организации, готовые места и сотрудники | DONE — FAIL (audit complete) | C:\\kidsmap; task33-progress; '+head+'; entry QA-only dirty; active_run NONE unchanged | [Отчёт](module02-2026-10-09-r1/REPORT.md), [evidence](module02-2026-10-09-r1/verification.json), [matrix](module02-2026-10-09-r1/matrix.csv), [screenshots](module02-2026-10-09-r1/screenshots-manifest.json) | 4 OPEN ORG-QA (3 P2, 1 P3); 216 tests OK; 308 PNG; external integrations/full suites NOT RUN; Далее 03; repair отдельным scope; [handoff](module02-2026-10-09-r1/next-chat.txt) |'
lines=before.splitlines(keepends=True);found=0
for i,line in enumerate(lines):
 if line.startswith(b'| 02 |'):
  tail=b'\r\n' if line.endswith(b'\r\n') else b'\n' if line.endswith(b'\n') else b''
  lines[i]=row.encode('utf-8')+tail;found+=1
assert found==1
after=b''.join(lines)
if journal.read_bytes()!=after:
 assert journal.read_bytes()==before,'Unexpected concurrent journal edit';journal.write_bytes(after)
diffrows=[i for i,(a,b) in enumerate(zip(before.splitlines(),after.splitlines())) if a!=b]
assert len(diffrows)==1 and before.splitlines()[diffrows[0]].startswith(b'| 02 |')
matrix=json.loads((h/'matrix.json').read_text(encoding='utf-8'));shots=json.loads((h/'screenshots-manifest.json').read_text(encoding='utf-8'))
assert len(matrix)==288 and len(shots)==308
assert all((h/r['screenshot']).exists() for r in matrix)
assert all(sha(h/r['file'])==r['sha256'] for r in shots)
secret=(state/'credential').read_text();secretfiles=[]
for p in h.rglob('*'):
 if p.is_file() and p.suffix in {'.py','.js','.txt','.md','.json','.jsonl','.log','.csv'}:
  if secret in p.read_text(encoding='utf-8',errors='ignore'):secretfiles.append(p.relative_to(h).as_posix())
assert not secretfiles,secretfiles
check=subprocess.run(['git','diff','--check'],cwd=root,capture_output=True,text=True);assert check.returncode==0,check.stdout
runtime=json.load(urllib.request.urlopen('http://localhost:8812/qa/version/'))
assert runtime['head']==head and runtime['source_digest']==s['source_digest'] and runtime['testing']
test=(h/'test.log').read_text(encoding='utf-8');assert 'Ran 216 tests' in test and '\nOK\n' in test
ledger=[json.loads(x) for x in (h/'setup-ledger.jsonl').read_text().splitlines()]
testexit=[x for x in ledger if 'test' in x['argv']][-1]['exit_code'];assert testexit==0
links=[]
for p in [h/'REPORT.md',h/'repair-prompts.md',h/'visual-review.md',*(h/'findings').glob('*.md')]:
 for url in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
  if '://' not in url and not url.startswith('#') and not (p.parent/url).exists() and (p.parent/url)!=h/'verification.json':links.append({'file':p.name,'target':url})
assert not links,links
status=subprocess.check_output(['git','status','--short'],cwd=root,text=True).splitlines()
assert all('docs/qa/module-acceptance-prompts.md' in x or 'docs/qa/module01-2026-10-09-r1/' in x or 'docs/qa/module02-2026-10-09-r1/' in x for x in status),status
containers=subprocess.check_output(['wsl','-d','Ubuntu-24.04','--','docker','ps','--format','{{.Names}}\t{{.Status}}\t{{.Ports}}'],text=True)
assert 'kidsmap-module01-20261009-r1' in containers and 'kidsmap-module02-20261009-r1' in containers
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'DONE — FAIL','checkout':str(root),'head':head,'branch':s['branch'],'final_worktree':status,'active_run':'NONE unchanged','source_files_compared':len(s['source_files']),'source_added_removed_changed':[],'module01_files_preserved':len(s['preserved_module01']),'active_marker_preserved':True,'journal_only_row02_changed':True,'journal_entry_sha256':s['entry_journal_sha256'],'journal_final_sha256':sha(journal),'test_count':216,'test_exit_code':testexit,'matrix':json.loads((h/'matrix-summary.json').read_text(encoding='utf-8')),'screenshots':len(shots),'screenshots_hash_verified':True,'credential_scan_matches':0,'git_diff_check_exit_code':check.returncode,'runtime':runtime,'container_names_status_ports':containers.splitlines(),'findings':['ORG-QA-01 P2','ORG-QA-02 P2','ORG-QA-03 P2','ORG-QA-04 P3'],'app_changes':False,'commit_push_deploy_production':False,'limits':'Full suites, production, external SDK/SMTP, OS-native selector visuals/assistive technology NOT RUN. No token/env/private production values.'}
(h/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:result[k] for k in ['decision','source_files_compared','module01_files_preserved','journal_only_row02_changed','test_count','test_exit_code','screenshots','app_changes','final_worktree']},ensure_ascii=False))
