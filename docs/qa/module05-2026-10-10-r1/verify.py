"""Verify actual own scope, foreign preservation and stand source; no cleanup."""
from pathlib import Path
import json,hashlib,subprocess,urllib.request,re,datetime,sys
P=Path(__file__).resolve().parent;R=P.parents[2]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap=json.loads((P/'snapshot.json').read_text(encoding='utf-8'));prior=json.loads((P/'preservation-entry.json').read_text(encoding='utf-8'));journal='docs/qa/module-acceptance-prompts.md'
source_changed=[p for p,sha in snap['source_files'].items() if not (R/p).is_file() or h(R/p)!=sha]
prior_changed=[p for p,sha in prior.items() if p!=journal and (not (R/p).is_file() or h(R/p)!=sha)]
before=(P/'journal-entry.txt').read_bytes().splitlines(keepends=True);after=(R/journal).read_bytes().splitlines(keepends=True)
changed=[i+1 for i,(a,b) in enumerate(zip(before,after)) if a!=b];target=next(i+1 for i,x in enumerate(before) if x.startswith(b'| 05 |'))
journal_ok=len(before)==len(after) and changed==[target] and after[target-1].startswith(b'| 05 |')
with urllib.request.urlopen('http://localhost:8816/qa/version/',timeout=10) as f:runtime=json.load(f)
credential=(R/'.tmp/module05-20261010-r1/credential').read_bytes();leaks=[]
for p in P.rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts and credential in p.read_bytes():leaks.append(p.relative_to(P).as_posix())
broken=[]
for p in P.rglob('*.md'):
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
  if link.startswith(('http:','https:','#','app:','codex:')):continue
  plain=re.sub(r':\d+$','',link.split('#')[0].strip('<>'))
  if plain in ['verification.json','verification-command.json'] and p.parent==P:continue
  if plain in ['../verification.json'] and p.parent==P/'findings':continue
  if not (Path(plain) if re.match(r'^[A-Za-z]:/',plain) else p.parent/plain).exists():broken.append({'file':p.relative_to(P).as_posix(),'target':link})
diff=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace')
status=subprocess.check_output(['git','status','--short'],cwd=R,text=True,encoding='utf-8').splitlines()
new_foreign=[p.relative_to(R).as_posix() for top in ['docs/qa','docs/superpowers/plans'] for p in (R/top).rglob('*') if p.is_file() and P not in p.parents and '__pycache__' not in p.parts and p.relative_to(R).as_posix() not in prior]
process_cmd=['powershell','-NoProfile','-Command',"$kmQaConnection=Get-NetTCPConnection -LocalPort 8816 -State Listen; $kmQaProcess=Get-CimInstance Win32_Process -Filter ('ProcessId='+$kmQaConnection.OwningProcess); [PSCustomObject]@{pid=$kmQaConnection.OwningProcess;command=$kmQaProcess.CommandLine;localAddress=$kmQaConnection.LocalAddress}|ConvertTo-Json -Compress"]
proc=subprocess.run(process_cmd,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace');process=json.loads(proc.stdout) if proc.returncode==0 else {'readback_exit':proc.returncode}
docker=subprocess.run(['wsl.exe','--','docker','inspect','kidsmap-module05-20261010-r1','--format','{{json .Mounts}}'],capture_output=True,text=True,encoding='utf-8',errors='replace')
mounts=json.loads(docker.stdout) if docker.returncode==0 else []
syntax=subprocess.run(['node',str(P/'check-js.cjs')],cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace');(P/'syntax-final.json').write_text(json.dumps({'command':['node',str(P/'check-js.cjs')],'exit_code':syntax.returncode,'output':syntax.stdout+syntax.stderr},indent=2),encoding='utf-8')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()
counts=json.loads((P/'results-summary.json').read_text(encoding='utf-8'))
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checkout':str(R),'git_root':subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=R,text=True).strip(),'head':head,'branch':branch,'source_files_checked':len(snap['source_files']),'source_changed':source_changed,'prior_files_checked_excluding_journal':len(prior)-1,'prior_changed':prior_changed,'new_foreign_files_preserved':new_foreign,'journal_changed_lines':changed,'journal_row05_only':journal_ok,'active_run':next(line.split(':',1)[1].strip() for line in (R/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if line.startswith('active_run:')),'active_run_file_unchanged':'docs/task33/implementation-status.md' not in prior_changed,'runtime':runtime,'runtime_source_digest_matches':runtime['source_digest']==snap['source_digest'],'runtime_head_matches':runtime['head']==snap['head'],'own_process':process,'own_mounts':mounts,'credential_scan_pass':not leaks,'credential_leak_files':leaks,'broken_local_links':broken,'git_diff_check_exit':diff.returncode,'git_diff_check_output':diff.stdout+diff.stderr,'qa_js_syntax_exit':syntax.returncode,'final_worktree':status,'counts':{k:v for k,v in counts.items() if k!='selected_runs'}}
result['pass']=not source_changed and not prior_changed and journal_ok and result['active_run_file_unchanged'] and result['active_run']==snap['active_run'] and result['runtime_source_digest_matches'] and result['runtime_head_matches'] and not leaks and not broken and diff.returncode==0 and syntax.returncode==0 and head==snap['head'] and branch==snap['branch'] and runtime['testing'] and 'run.py' in process.get('command','') and 'serve' in process.get('command','')
result['own_scope_integrity_pass']=not source_changed and journal_ok and result['active_run_file_unchanged'] and result['active_run']==snap['active_run'] and result['runtime_source_digest_matches'] and result['runtime_head_matches'] and not leaks and not broken and diff.returncode==0 and syntax.returncode==0 and head==snap['head'] and branch==snap['branch'] and runtime['testing'] and 'run.py' in process.get('command','') and 'serve' in process.get('command','')
result['all_prior_bytes_unchanged']=not prior_changed
result['preservation_status']='CONCURRENT FOREIGN DRIFT OBSERVED; no rollback or overwrite' if prior_changed else 'ENTRY BYTES UNCHANGED'
result['foreign_drift']=[{'path':p,'entry_sha256':prior[p],'current_sha256':h(R/p) if (R/p).is_file() else None,'current_mtime_utc':datetime.datetime.fromtimestamp((R/p).stat().st_mtime,datetime.timezone.utc).isoformat() if (R/p).is_file() else None,'origin':'UNKNOWN; outside this run ownership; no content copied'} for p in prior_changed]
(P/'verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
(P/'verification-command.json').write_text(json.dumps({'command':f'.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/verify.py','exit_code':0 if result['pass'] else 1},indent=2),encoding='utf-8')
print(json.dumps({k:result[k] for k in ['pass','head','branch','source_files_checked','source_changed','prior_files_checked_excluding_journal','prior_changed','journal_changed_lines','active_run','credential_scan_pass','broken_local_links','git_diff_check_exit','qa_js_syntax_exit','counts']},ensure_ascii=True));raise SystemExit(0 if result['pass'] else 1)
