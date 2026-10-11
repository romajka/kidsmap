"""Scoped journal update plus preservation verification; no application mutations."""
from pathlib import Path
import json,hashlib,subprocess,urllib.request,re
P=Path(__file__).resolve().parent;R=P.parents[2]
foreign=json.loads((P/'foreign-entry.json').read_text())
journal=R/'docs/qa/module-acceptance-prompts.md'
raw=journal.read_bytes();lines=raw.splitlines(keepends=True)
old=next(line for line in lines if line.startswith(b'| 01 |'))
before=P/'journal-row01-before.txt'
if before.exists():
 original=raw.replace(old,before.read_bytes(),1)
 assert hashlib.sha256(original).hexdigest()==foreign['docs/qa/module-acceptance-prompts.md']
else:
 assert hashlib.sha256(raw).hexdigest()==foreign['docs/qa/module-acceptance-prompts.md']
 before.write_bytes(old)
newline=b'\r\n' if old.endswith(b'\r\n') else b'\n'
row='| 01 | Постоянные места | DONE — FAIL (scoped recheck: PLACE-QA-01–07 PASS; RU district P3 OPEN; full limits NOT RUN) | C:\\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; dirty WORKTREE preserved; active_run NONE; new localhost:8841 + isolated fresh PO/MO | [Fresh recheck 2026-10-11](module01-recheck-2026-10-11-r1/REPORT.md), [verification](module01-recheck-2026-10-11-r1/verification.json), [matrix](module01-recheck-2026-10-11-r1/matrix.csv), [screenshots](module01-recheck-2026-10-11-r1/screenshots-manifest.json); [история r2](module01-2026-10-09-r2/REPORT.md), [r1](module01-2026-10-09-r1/REPORT.md) | 7 existing fixes verified in WORKTREE/fresh locale profile; 38 Django +34 Node +9 locale-helper PASS; browser252P/6F(one cause)/12NR;164 native PNG; remaining PLACE-QA-08 alias CROSS-QA-03; full module acceptance NOT RUN; [repair prompt](module01-recheck-2026-10-11-r1/PLACE-QA-08-repair.txt), [handoff](module01-recheck-2026-10-11-r1/next-chat.txt) |'
journal.write_bytes(raw.replace(old,row.encode('utf-8')+newline,1))
changed=[];missing=[]
for path,sha in foreign.items():
 if path=='docs/qa/module-acceptance-prompts.md':continue
 f=R/path
 if not f.is_file():missing.append(path)
 elif hashlib.sha256(f.read_bytes()).hexdigest()!=sha:changed.append(path)
snap=json.loads((P/'snapshot.json').read_text());source_matches=all(hashlib.sha256((R/path).read_bytes()).hexdigest()==sha for path,sha in snap['source_files'].items())
now=journal.read_bytes().splitlines(keepends=True)
other_rows_match=b''.join(x for x in lines if not x.startswith(b'| 01 |'))==b''.join(x for x in now if not x.startswith(b'| 01 |'))
active=next(x.split(':',1)[1].strip() for x in (R/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if x.startswith('active_run:'))
version=json.load(urllib.request.urlopen('http://localhost:8841/qa/version/'))
expected={8827:2428,8828:2072,8829:9988,8830:17768,8831:23204}
cmd="Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in 8827,8828,8829,8830,8831 } | Select-Object LocalPort,OwningProcess | ConvertTo-Json"
listeners=json.loads(subprocess.check_output(['pwsh','-NoProfile','-Command',cmd],text=True))
actual={r['LocalPort']:r['OwningProcess'] for r in listeners}
containers=subprocess.check_output(['wsl.exe','--','docker','ps','--format','{{.ID}} {{.Names}}'],text=True)
checks={'foreign_files_preserved_except_authorized_row01':not changed and not missing,'other_journal_bytes_preserved':other_rows_match,'application_source_files_preserved':source_matches,'active_run_preserved':active==snap['active_run']=='NONE','head_preserved':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==snap['head'],'branch_preserved':subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()==snap['branch'],'running_source_attested':version['entry_matches_startup'] and version['startup_matches_disk'] and version['current_digest']==snap['source_digest'],'foreign_listener_pids_preserved':actual==expected,'foreign_containers_preserved':all(s in containers for s in ['2f5fcdd7919e kidsmap-module11-20261011-r1','e18876a6e61f kidsmap-module12-20261011-r1','3901fd737297 kidsmap-module13-20261011-r1']),'final_browser_scripts_complete':all(not json.loads((P/(n+'.result.txt')).read_text(encoding='utf-8')).get('error') for n in ['place-flow','review','mixed-price','map','nature','admin-matrix','labels','public','residual','visual-diagnostics'])}
credential=(R/'.tmp/module01-recheck-20261011-r1/credential').read_text()
secret_files=[f.relative_to(P).as_posix() for f in P.rglob('*') if f.is_file() and f.suffix in ['.py','.js','.txt','.json','.jsonl','.md','.csv'] and credential.encode() in f.read_bytes()]
checks['local_password_absent_from_report_artifacts']=not secret_files
v={'checks':checks,'passed':sum(checks.values()),'total':len(checks),'foreign_entry_files':len(foreign),'changed_foreign':changed,'missing_foreign':missing,'source_files':len(snap['source_files']),'source_digest':snap['source_digest'],'runtime':version,'active_run':active,'foreign_listeners':actual,'containers':containers.splitlines(),'password_leak_paths':secret_files,'scope':'row01 only; all previous reports and application sources preserved'}
(P/'verification.json').write_text(json.dumps(v,indent=2))
(P/'runtime-version-final.json').write_text(json.dumps(version,indent=2))
print(json.dumps({'checks':checks,'foreign_files':len(foreign),'source_files':len(snap['source_files'])}))
assert all(checks.values()),v
