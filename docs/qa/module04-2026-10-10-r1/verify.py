"""Own scope preservation verification. New foreign files are inventoried, never edited."""
from pathlib import Path
import json,hashlib,subprocess,urllib.request,re,datetime
P=Path(__file__).resolve().parent;R=P.parents[2]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap=json.loads((P/'snapshot.json').read_text());prior=json.loads((P/'preservation-entry.json').read_text());extra=json.loads((P/'snapshot-templates.json').read_text());journal='docs/qa/module-acceptance-prompts.md'
source_changed=[p for p,sha in {**snap['source_files'],**extra}.items() if not (R/p).is_file() or h(R/p)!=sha]
prior_changed=[p for p,sha in prior.items() if p!=journal and (not (R/p).is_file() or h(R/p)!=sha)]
before=(P/'journal-entry.txt').read_bytes().splitlines(keepends=True);after=(R/journal).read_bytes().splitlines(keepends=True)
changed=[i+1 for i,(a,b) in enumerate(zip(before,after)) if a!=b];target=next(i+1 for i,x in enumerate(before) if x.startswith(b'| 04 |'))
journal_ok=len(before)==len(after) and changed==[target] and after[target-1].startswith(b'| 04 |')
active=(R/'docs/task33/implementation-status.md').read_text(encoding='utf-8');active_none=bool(re.search(r'active_run.*NONE',active))
with urllib.request.urlopen('http://localhost:8815/qa/version/',timeout=10) as f:runtime=json.load(f)
credential=(R/'.tmp/module04-20261010-r1/credential').read_bytes();leaks=[]
for p in P.rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts and credential in p.read_bytes():leaks.append(p.relative_to(P).as_posix())
broken=[]
for p in [P/'REPORT.md',*(P/'findings').glob('*.md')]:
 if not p.exists():continue
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
  if not link.startswith(('http:','https:','#','C:/')) and not (p.parent/link.split('#')[0]).exists():broken.append({'file':p.name,'target':link})
diff=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True)
new_foreign=[p.relative_to(R).as_posix() for p in (R/'docs/qa').rglob('*') if p.is_file() and P not in p.parents and '__pycache__' not in p.parts and p.relative_to(R).as_posix() not in prior]
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip(),'source_files_checked':len(snap['source_files']),'extra_root_templates_checked':len(extra),'source_changed':source_changed,'prior_files_checked_excluding_journal':len(prior)-1,'prior_changed':prior_changed,'new_foreign_qa_files_preserved':new_foreign,'journal_changed_lines':changed,'journal_row04_only':journal_ok,'active_run_NONE_unchanged':active_none and 'docs/task33/implementation-status.md' not in prior_changed,'runtime':runtime,'runtime_source_digest_matches':runtime['source_digest']==snap['source_digest'],'runtime_head_matches':runtime['head']==snap['head'],'credential_scan_pass':not leaks,'credential_leak_files':leaks,'broken_local_links':broken,'git_diff_check_exit':diff.returncode,'git_diff_check_output':diff.stdout+diff.stderr,'final_worktree':subprocess.check_output(['git','status','--short'],cwd=R,text=True).splitlines()}
result['pass']=not source_changed and not prior_changed and journal_ok and result['active_run_NONE_unchanged'] and result['runtime_source_digest_matches'] and result['runtime_head_matches'] and not leaks and not broken and diff.returncode==0 and result['head']==snap['head']
(P/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=True));raise SystemExit(0 if result['pass'] else 1)
