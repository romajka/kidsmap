"""Final fresh preservation/runtime/artifact verification. No app imports or mutations."""
from pathlib import Path
import json,hashlib,ast,subprocess,re,urllib.request,datetime
from PIL import Image
P=Path(__file__).resolve().parent;R=P.parents[2];issues=[]
def check(ok,message):
 if not ok:issues.append(message)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((P/name).read_text(encoding='utf-8'))
snap=read('snapshot.json');prior=read('preservation-entry.json');journal=R/'docs/qa/module-acceptance-prompts.md'
for path,value in prior.items():
 if path=='docs/qa/module-acceptance-prompts.md':continue
 check((R/path).is_file() and sha(R/path)==value,'Foreign drift: '+path)
old=(P/'journal-entry.txt').read_bytes().splitlines(keepends=True);now=journal.read_bytes().splitlines(keepends=True)
check([x for x in old if not x.startswith(b'| 12 |')]==[x for x in now if not x.startswith(b'| 12 |')],'Journal outside row12 changed')
check(any(x.startswith(b'| 12 |') and b'DONE' in x for x in now),'Journal12 notdone');check(any(x.startswith(b'| 13 |') and b'NOT RUN' in x for x in now),'Journal13 changed')
for path,value in snap['source_files'].items():check((R/path).is_file() and sha(R/path)==value,'Source drift: '+path)
active=next(line.split(':',1)[1].strip() for line in (R/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if line.startswith('active_run:'));check(active==snap['active_run'],'active_run drift')
check(subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==snap['head'],'HEAD drift');check(subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()==snap['branch'],'branch drift')
files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=R,text=True).splitlines();new_foreign=[x for x in files if x not in prior and P not in (R/x).parents and (R/x).is_file() and '__pycache__' not in x and not Path(x).name.startswith('.env')];check(not new_foreign,'New unowned files '+str(new_foreign[:10]))
runtime={}
for port in [8829,8830]:
 try:
  with urllib.request.urlopen(f'http://localhost:{port}/qa/version/',timeout=25) as response:v=json.load(response)
  runtime[str(port)]=v;check(v['testing'] and v['entry_matches_startup'] and v['startup_matches_disk'] and v['current_digest']==snap['source_digest'],f'Runtime source mismatch {port}')
 except Exception as e:issues.append(f'Runtime check {port}: {type(e).__name__}')
entry=read('stands-entry.json');ps="ConvertTo-Json -InputObject @(Get-NetTCPConnection -State Listen | Where-Object { ($_.LocalPort -ge 8810 -and $_.LocalPort -le 8835) -or ($_.LocalPort -ge 55431 -and $_.LocalPort -le 55445) } | Select-Object LocalAddress,LocalPort,OwningProcess) -Compress"
result=subprocess.run(['powershell','-NoProfile','-Command',ps],capture_output=True,text=True);current=json.loads(result.stdout);check(result.returncode==0,'TCP inventory failed')
for oldstand in entry['http']:
 if oldstand['LocalPort'] in [8827,8828]:check(any(x['LocalPort']==oldstand['LocalPort'] and x['OwningProcess']==oldstand['OwningProcess'] for x in current),'Foreign HTTP PID changed '+str(oldstand['LocalPort']))
containers=subprocess.run(['wsl.exe','--','docker','ps','--format','{{.Names}} {{.ID}} {{.Ports}}'],capture_output=True,text=True);check(containers.returncode==0,'docker inventory failed')
for line in entry['docker']:check(line in containers.stdout.splitlines(),'Foreign Docker identity/ports changed')
foreignmount=subprocess.run(['wsl.exe','--','docker','inspect','--format','{{range .Mounts}}{{.Name}}{{end}}','kidsmap-module11-20261011-r1'],capture_output=True,text=True);check(foreignmount.stdout.strip()=='e77bec37ee83741b05ff9f14c82631c05c2c428d0a56c88d559465b69511487d','Foreign volume changed')
manifest=read('screenshots-manifest.json');counts=read('counts.json');rows=read('matrix.json');check(len(manifest)==counts['native_png'],'PNG count mismatch');check({s:sum(x['status']==s for x in rows) for s in ['PASS','FAIL','NOT RUN']}==counts['normalized_observations'],'matrix counts mismatch')
for x in manifest:
 path=P/x['path'];check(path.is_file() and sha(path)==x['sha256'],'PNG drift '+x['path'])
 with Image.open(path) as im:check(im.size==(x['width'],x['height']),'PNG dimensions '+x['path']);im.verify()
check(len(list((P/'findings').glob('ANALYTICS-QA-*.md')))==8,'Finding count');check(len(list((P/'findings').glob('*-repair.txt')))==8,'Repair prompt count')
for path in P.rglob('*.py'):
 if '__pycache__' not in path.parts:
  try:ast.parse(path.read_text(encoding='utf-8'))
  except SyntaxError as e:issues.append('QA Python syntax '+str(path.relative_to(P)))
js=subprocess.run(['C:/Program Files/nodejs/node.exe',str(P/'check-js.cjs')],cwd=R,capture_output=True,text=True);check(js.returncode==0,'QA JS syntax '+js.stdout[:150])
for path in P.rglob('*.json'):
 if '__pycache__' not in path.parts:
  try:json.loads(path.read_text(encoding='utf-8'))
  except Exception:issues.append('JSON parse '+str(path.relative_to(P)))
credential=(R/'.tmp/module12-20261011-r1/credential').read_text();text_files=0
for path in P.rglob('*'):
 if path.is_file() and path.suffix in ['.md','.txt','.json','.jsonl','.py','.js','.cjs','.csv','.log'] and '__pycache__' not in path.parts:
  text_files+=1;content=path.read_text(encoding='utf-8',errors='replace');check(credential not in content,'QA credential in artifact '+str(path.relative_to(P)))
for path in [P/'REPORT.md',P/'FINDINGS.md',P/'COMMANDS.md',*(P/'findings').glob('*.md')]:
 for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
  if target.startswith(('http:','https:','#')):continue
  check((path.parent/target.split('#')[0]).exists(),'Broken link '+str(path.relative_to(P))+': '+target)
diff=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True);check(diff.returncode==0,'git diff --check failed')
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':1 if issues else 0,'issues':issues,'foreign_files_checked':len(prior)-1,'source_files_checked':len(snap['source_files']),'active_run':active,'head':snap['head'],'branch':snap['branch'],'runtime':runtime,'foreign_HTTP_preserved':[x for x in current if x['LocalPort'] in [8827,8828]],'foreign_containers_preserved':all(x in containers.stdout.splitlines() for x in entry['docker']),'foreign_volume_preserved':foreignmount.stdout.strip()=='e77bec37ee83741b05ff9f14c82631c05c2c428d0a56c88d559465b69511487d','native_png_checked':len(manifest),'normalized_observations':counts['normalized_observations'],'text_secret_scan_files':text_files,'js_syntax_exit':js.returncode,'git_diff_check_exit':diff.returncode,'new_unowned_files':new_foreign}
(P/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k in ['exit_code','issues','foreign_files_checked','source_files_checked','native_png_checked','normalized_observations','js_syntax_exit','git_diff_check_exit']},ensure_ascii=False));raise SystemExit(result['exit_code'])
