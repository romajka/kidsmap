"""Final read-only checks, own report scope and foreign drift. Never restore bytes."""
from pathlib import Path
import json,hashlib,subprocess,urllib.request,re,datetime,sys,ast
P=Path(__file__).resolve().parent;R=P.parents[2];sys.stdout.reconfigure(encoding='utf-8')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap=json.loads((P/'snapshot.json').read_text(encoding='utf-8'));prior=json.loads((P/'preservation-entry.json').read_text(encoding='utf-8'));journal='docs/qa/module-acceptance-prompts.md'
source_changed=[p for p,sha in snap['source_files'].items() if not (R/p).is_file() or h(R/p)!=sha]
prior_changed=[p for p,sha in prior.items() if p!=journal and (not (R/p).is_file() or h(R/p)!=sha)]
before=(P/'journal-entry.txt').read_bytes().splitlines(keepends=True);after=(R/journal).read_bytes().splitlines(keepends=True)
changed=[i+1 for i,(a,b) in enumerate(zip(before,after)) if a!=b];target=next(i+1 for i,x in enumerate(before) if x.startswith(b'| 06 |'))
journal_ok=len(before)==len(after) and changed==[target] and after[target-1].startswith(b'| 06 |')
runtime=[]
for port in [8817,8818]:
 with urllib.request.urlopen(f'http://localhost:{port}/qa/version/',timeout=15) as f:runtime.append({'port':port,**json.load(f)})
credential=(R/'.tmp/module06-20261010-r1/credential').read_bytes();leaks=[]
for p in P.rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts and credential in p.read_bytes():leaks.append(p.relative_to(P).as_posix())
broken=[]
for p in P.rglob('*.md'):
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
  if link.startswith(('http:','https:','#','app:','codex:')):continue
  plain=re.sub(r':\d+$','',link.split('#')[0].strip('<>'))
  if plain in ['verification.json','verification-command.json'] and p.parent==P:continue
  if not (Path(plain) if re.match(r'^[A-Za-z]:/',plain) else p.parent/plain).exists():broken.append({'file':p.relative_to(P).as_posix(),'target':link})
diff=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace')
status=subprocess.check_output(['git','status','--short'],cwd=R,text=True,encoding='utf-8').splitlines()
new_foreign=[p.relative_to(R).as_posix() for top in ['docs/qa','docs/superpowers/plans'] for p in (R/top).rglob('*') if p.is_file() and P not in p.parents and '__pycache__' not in p.parts and p.relative_to(R).as_posix() not in prior]
ps=r"$kmPorts=@(8811,8812,8815,8816,8817,8818); $kmRows=@(Get-NetTCPConnection -State Listen | Where-Object { $kmPorts -contains $_.LocalPort } | ForEach-Object { $kmRow=[ordered]@{port=$_.LocalPort;pid=$_.OwningProcess;address=$_.LocalAddress}; if ($_.LocalPort -in @(8817,8818)) { $kmProc=Get-CimInstance Win32_Process -Filter ('ProcessId='+$_.OwningProcess);$kmRow.command=$kmProc.CommandLine }; [PSCustomObject]$kmRow }); ConvertTo-Json -InputObject $kmRows -Compress"
proc=subprocess.run(['powershell','-NoProfile','-Command',ps],cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace');processes=json.loads(proc.stdout) if proc.returncode==0 else []
foreign_entry={8811:6112,8812:40848,8815:43232,8816:40212};foreign_process_match=all(any(x['port']==port and x['pid']==pid for x in processes) for port,pid in foreign_entry.items())
docker=subprocess.run(['wsl.exe','--','docker','inspect','kidsmap-module06-20261010-r1','--format','{{json .Mounts}}'],capture_output=True,text=True,encoding='utf-8',errors='replace');mounts=json.loads(docker.stdout) if docker.returncode==0 else []
containers=subprocess.run(['wsl.exe','--','docker','ps','--format','{{.Names}}'],capture_output=True,text=True,encoding='utf-8',errors='replace');names=containers.stdout.splitlines();foreign_containers=['kidsmap-placeqa06-plan-20261010','kidsmap-module05-20261010-r1','kidsmap-module04-20261010-r1','kidsmap-module03-20261010-r1','kidsmap-module01-20261009-r2','kidsmap-module02-20261009-r1','kidsmap-module01-20261009-r1','kidsmap-manual-portable']
syntax=subprocess.run(['C:/Program Files/nodejs/node.exe',str(P/'check-js.cjs')],cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace');py_errors=[]
for p in P.glob('*.py'):
 try:ast.parse(p.read_text(encoding='utf-8'))
 except SyntaxError as exc:py_errors.append({'file':p.name,'error':str(exc)})
(P/'syntax-final.json').write_text(json.dumps({'js_command':['C:/Program Files/nodejs/node.exe',str(P/'check-js.cjs')],'js_exit_code':syntax.returncode,'js_output':syntax.stdout+syntax.stderr,'python_ast_files':len(list(P.glob('*.py'))),'python_ast_errors':py_errors},indent=2),encoding='utf-8')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip();counts=json.loads((P/'results-summary.json').read_text(encoding='utf-8'));active=next(line.split(':',1)[1].strip() for line in (R/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if line.startswith('active_run:'))
runtime_ok=all(x['source_digest']==snap['source_digest'] and x['head']==head and x['testing'] for x in runtime)
process_ok=all(any(x['port']==port and script in x.get('command','') and x['address']=='127.0.0.1' for x in processes) for port,script in [(8817,'run.py'),(8818,'run-configured.py')])
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checkout':str(R),'head':head,'branch':branch,'source_files_checked':len(snap['source_files']),'source_changed':source_changed,'prior_files_checked_excluding_journal':len(prior)-1,'prior_changed':prior_changed,'new_foreign_files_preserved':new_foreign,'journal_changed_lines':changed,'journal_row06_only':journal_ok,'active_run':active,'active_run_file_unchanged':'docs/task33/implementation-status.md' not in prior_changed,'runtime':runtime,'runtime_matches_worktree_snapshot':runtime_ok,'runtime_proof_limit':'qa/version echoes manifest; proof also requires startup hash guard in both launchers + current 2784 file hash comparison + actual listener command/import path and native UI. Production UNKNOWN.','processes':processes,'own_listener_check':process_ok,'foreign_listener_pids_match_entry':foreign_process_match,'own_mounts':mounts,'own_mounts_read_exit':docker.returncode,'container_names_read_exit':containers.returncode,'running_container_names':names,'expected_foreign_container_names':foreign_containers,'missing_expected_foreign_containers':[x for x in foreign_containers if x not in names],'credential_scan_pass':not leaks,'credential_leak_files':leaks,'broken_local_links':broken,'git_diff_check_exit':diff.returncode,'git_diff_check_output':diff.stdout+diff.stderr,'qa_js_syntax_exit':syntax.returncode,'qa_python_syntax_errors':py_errors,'final_worktree':status,'counts':{k:v for k,v in counts.items() if k!='selected_runs'}}
result['own_scope_integrity_pass']=not source_changed and journal_ok and result['active_run_file_unchanged'] and active==snap['active_run'] and runtime_ok and process_ok and not leaks and not broken and not counts['unclassified_fail_rows'] and diff.returncode==0 and syntax.returncode==0 and not py_errors and head==snap['head'] and branch==snap['branch']
result['all_prior_bytes_unchanged']=not prior_changed
result['preservation_status']='FOREIGN DRIFT OBSERVED; origin UNKNOWN, no rollback/overwrite' if prior_changed else 'ENTRY BYTES UNCHANGED'
result['foreign_drift']=[{'path':p,'entry_sha256':prior[p],'current_sha256':h(R/p) if (R/p).is_file() else None,'current_mtime_utc':datetime.datetime.fromtimestamp((R/p).stat().st_mtime,datetime.timezone.utc).isoformat() if (R/p).is_file() else None,'origin':'UNKNOWN; outside own ownership; contents not copied'} for p in prior_changed]
result['pass']=result['own_scope_integrity_pass'] and result['all_prior_bytes_unchanged'] and foreign_process_match
(P/'verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8');(P/'verification-command.json').write_text(json.dumps({'command':'.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/verify.py','exit_code':0 if result['pass'] else 1},indent=2),encoding='utf-8')
print(json.dumps({k:result[k] for k in ['pass','own_scope_integrity_pass','source_files_checked','source_changed','prior_changed','journal_changed_lines','active_run','credential_scan_pass','broken_local_links','own_listener_check','foreign_listener_pids_match_entry']},ensure_ascii=True));raise SystemExit(0 if result['pass'] else 1)
