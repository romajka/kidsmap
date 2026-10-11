"""Fresh final preservation/source/runtime/link/screenshot/secret verification."""
from pathlib import Path
import json,hashlib,subprocess,re,ast,datetime,sys,urllib.request
sys.stdout.reconfigure(encoding='utf-8');P=Path(__file__).resolve().parent;R=P.parents[2]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def shell(cmd):return subprocess.run(['powershell','-NoProfile','-Command',cmd],cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace')
snap=json.loads((P/'snapshot.json').read_text());source={p.relative_to(R).as_posix():h(p) for top in ['src','static','config','locale','templates'] for p in (R/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
current=json.loads((P/'current-snapshot.json').read_text(encoding='utf-8'))
prior=json.loads((P/'preservation-entry.json').read_text());journal='docs/qa/module-acceptance-prompts.md';drift=[f for f,sha in prior.items() if f!=journal and (not (R/f).is_file() or h(R/f)!=sha)]
old=(P/'journal-entry.txt').read_text(encoding='utf-8').splitlines();new=(R/journal).read_text(encoding='utf-8').splitlines();changed=[i+1 for i,(a,b) in enumerate(zip(old,new)) if a!=b];journal_ok=len(old)==len(new) and len(changed)==1 and new[changed[0]-1].startswith('| 10 |')
pw=(R/'.tmp/module10-20261010-r1/credential').read_text();leaks=[];syntax=[];broken=[]
for f in P.rglob('*'):
 if not f.is_file() or '__pycache__' in f.parts or f.suffix in ['.png','.jpg']:continue
 try:s=f.read_text(encoding='utf-8-sig')
 except UnicodeDecodeError:continue
 if pw in s:leaks.append(f.relative_to(P).as_posix())
 if f.suffix=='.py':
  try:ast.parse(s)
  except SyntaxError as e:syntax.append({'file':f.name,'error':str(e)})
 if f.suffix=='.md':
  for link in re.findall(r'\]\(([^)]+)\)',s):
   if link.startswith(('http','#','mailto')):continue
   target=link.split('#')[0].strip('<>')
   if target and target not in ['verification.json','runtime-final.json'] and not (f.parent/target).exists():broken.append({'file':f.relative_to(P).as_posix(),'target':target})
q=shell("ConvertTo-Json -InputObject @(Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -ge 8810 -and $_.LocalPort -le 8830 } | Select-Object LocalAddress,LocalPort,OwningProcess) -Compress");http=json.loads(q.stdout)
d=subprocess.run(['wsl.exe','--','docker','ps','--format','{{.Names}} {{.ID}} {{.Ports}}'],cwd=R,capture_output=True,text=True,encoding='utf-8');containers=d.stdout.splitlines();entry=json.loads((P/'stands-entry.json').read_text());foreign_http=[f for f in entry['http'] if 8810<=f['LocalPort']<=8830]
preserved_http=all(any(y==f for y in http) for f in foreign_http);preserved_docker=all(f in containers for f in entry['docker'])
inspect=subprocess.run(['wsl.exe','--','docker','inspect','--format','{{.Id}} {{.Config.Image}} {{range .Mounts}}{{.Name}} {{.Destination}}{{end}}','kidsmap-module10-20261010-r1'],cwd=R,capture_output=True,text=True)
owner=shell("ConvertTo-Json -InputObject @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -in 40936,17432,40836,40732 } | ForEach-Object { [PSCustomObject]@{ PID=$_.ProcessId; OwnLauncher=[bool]($_.CommandLine -match 'module10-2026-10-10-r1[\\/]run(-current)?.py'); NoAutoreloader=[bool]($_.CommandLine -notmatch '--noreload-child') } }) -Compress")
owners=json.loads(owner.stdout)
native_syntax=subprocess.run(['C:/Program Files/nodejs/node.exe',str(P/'check-js.cjs')],capture_output=True,text=True,encoding='utf-8',errors='replace')
diff=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()
app_diff=subprocess.check_output(['git','diff','--name-only','--','src','static','config','locale','templates'],cwd=R,text=True).splitlines()
runtime={}
for port,pid in [(8823,40936),(8824,17432),(8825,40836),(8826,40732)]:
 with urllib.request.urlopen(f'http://localhost:{port}/qa/version/',timeout=10) as response:version=json.load(response)
 expected=current if port in [8825,8826] else snap
 ok=version['testing'] and version['head']==head==expected['head'] and version['source_digest']==expected['source_digest'] and any(f['LocalPort']==port and f['OwningProcess']==pid for f in http) and any(o['PID']==pid and o['OwnLauncher'] for o in owners)
 runtime[str(port)]={'pid':pid,'version':version,'startup_manifest_match':ok,'current_worktree_match':ok and port in [8825,8826] and source==current['source_files'],'note':'Entry-imports/disk drift: not current attestation' if port in [8823,8824] else 'New matched current snapshot guard / no autoreloader'}
with urllib.request.urlopen('http://localhost:8825/qa/state/',timeout=10) as response:state=json.load(response)
(P/'state-final.json').write_text(json.dumps(state,indent=2,ensure_ascii=False),encoding='utf-8')
runtime.update(source_evidence='Startup run.py full source guard, use_reloader=False, listener PID and current source manifest. qa/version echoes manifest, not independent attestation.',container_inspection=inspect.stdout.strip(),browser='Chromium153.0.8010.12 / module10-r1 / headless shell1243',isolation='DJANGO_TESTING1; own PG55441/module10/test_module10; own LocMem/cache/mail/media/private-media/cookies; no dotenv/credentials/external transports',process_identity=owners)
(P/'runtime-final.json').write_text(json.dumps(runtime,indent=2),encoding='utf-8')
for filename in ['runtime-final.json','state-final.json']:
 if pw in (P/filename).read_text(encoding='utf-8'):leaks.append(filename)
pngs=json.loads((P/'screenshots-manifest.json').read_text());png_drift=[x['path'] for x in pngs if not (P/x['path']).is_file() or h(P/x['path'])!=x['sha256']]
finding_source_missing=[];evidence_missing=[]
for f in json.loads((P/'findings.json').read_text(encoding='utf-8')):
 for src in f['source']:
  name=re.sub(r':\d+$','',src)
  if not (R/name).is_file():finding_source_missing.append({'id':f['id'],'path':name})
 for ev in f['evidence']:
  if not (P/ev).is_file():evidence_missing.append({'id':f['id'],'path':ev})
ledger=[json.loads(l) for l in (P/'command-ledger.jsonl').read_text().splitlines()];final_scripts=['matrix-empty','settings','matrix-filled','flags','acl','keyboard','media-errors','finish','faq-proof','modal-proof','organization-proof','network-proof','visual-final','focus-proof','current-settings','current-matrix','current-focus','current-boundary','current-pages','current-network','current-console','current-concurrency'];cli_final_bad=[]
for name in final_scripts:
 matching=[x for x in ledger if x['result']==name+'.result.txt']
 if not matching or matching[-1]['cli_exit_code']!=0:cli_final_bad.append(name)
settings=state['settings'];fixture_restore=settings['events_section_enabled'] and settings['specialists_section_enabled'] and settings['organizations_section_enabled'] and not settings['public_favorites_count_enabled'] and bool(settings['logo']) and settings['home_title_en']=='QA10-HERO-EN'
readback=json.loads((P/'current-organization-readback.json').read_text(encoding='utf-8'));native_candidate=readback['candidate']['status']=='draft' and readback['candidate']['names']['name_az']=='Uydurma QA10 admin: CURRENT OFF candidate' and readback['live']['content_version']==1 and readback['live']['name_az']=='Uydurma QA10 admin təşkilatı'
expected_diff=sorted(x['path'] for x in current['entry_changed']);recorded_delta_preserved=sorted(app_diff)==expected_diff and source==current['source_files']
summary={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':head,'branch':branch,'source_files':len(source),'entry_source_unchanged':source==snap['source_files'],'current_source_unchanged':source==current['source_files'],'source_digest':hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),'application_diff':app_diff,'recorded_foreign_source_changed':len(current['entry_changed']),'recorded_foreign_source_added':len(current['entry_added']),'recorded_source_delta_preserved':recorded_delta_preserved,'foreign_files_checked':len(prior)-1,'foreign_drift':drift,'journal_only_row10':journal_ok,'journal_changed_lines':changed,'active_run_unchanged':h(R/'docs/task33/implementation-status.md')==prior['docs/task33/implementation-status.md'],'foreign_http_count':len({f['LocalPort'] for f in foreign_http}),'foreign_http_preserved':preserved_http,'foreign_docker_count':len(entry['docker']),'foreign_docker_preserved':preserved_docker,'http_final':http,'docker_final':containers,'known_credential_leaks':leaks,'python_ast_errors':syntax,'js_syntax_exit':native_syntax.returncode,'broken_report_links':broken,'finding_source_missing':finding_source_missing,'finding_evidence_missing':evidence_missing,'screenshot_count':len(pngs),'screenshot_drift':png_drift,'final_browser_scripts_nonzero':cli_final_bad,'git_diff_check_exit':diff.returncode,'current_runtime_match':all(runtime[str(port)]['current_worktree_match'] for port in [8825,8826]),'entry_runtime_not_current':[8823,8824],'own_fixture_settings_restored':fixture_restore,'native_org_candidate_live_proof':native_candidate}
ok=summary['current_source_unchanged'] and recorded_delta_preserved and not drift and journal_ok and summary['active_run_unchanged'] and preserved_http and preserved_docker and not leaks and not syntax and not broken and not finding_source_missing and not evidence_missing and not png_drift and not cli_final_bad and native_syntax.returncode==0 and diff.returncode==0 and summary['current_runtime_match'] and branch==snap['branch'] and fixture_restore and native_candidate and q.returncode==d.returncode==inspect.returncode==owner.returncode==0
summary['status']='PASS' if ok else 'FAIL';(P/'verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in summary.items() if k not in ['http_final','docker_final']},ensure_ascii=False));sys.exit(0 if ok else 1)
