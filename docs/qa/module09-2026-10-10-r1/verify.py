"""Final preservation, source identity, screenshot/link/secret checks."""
from pathlib import Path
import json,hashlib,subprocess,re,ast,datetime,sys,urllib.request
sys.stdout.reconfigure(encoding='utf-8');P=Path(__file__).resolve().parent;R=P.parents[2]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
x=json.loads((P/'snapshot.json').read_text());source={p.relative_to(R).as_posix():h(p) for top in ['src','static','config','locale','templates'] for p in (R/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
prior=json.loads((P/'preservation-entry.json').read_text());journal='docs/qa/module-acceptance-prompts.md';drift=[f for f,sha in prior.items() if f!=journal and (not (R/f).is_file() or h(R/f)!=sha)]
old=(P/'journal-entry.txt').read_text(encoding='utf-8').splitlines();new=(R/journal).read_text(encoding='utf-8').splitlines();changed=[i+1 for i,(a,b) in enumerate(zip(old,new)) if a!=b];journal_ok=len(old)==len(new) and len(changed)==1 and new[changed[0]-1].startswith('| 09 |')
pw=(R/'.tmp/module09-20261010-r1/credential').read_text();leaks=[];syntax=[];broken=[]
for f in P.rglob('*'):
 if not f.is_file() or '__pycache__' in f.parts or f.suffix in ['.png','.jpg']:continue
 try:s=f.read_text(encoding='utf-8-sig')
 except UnicodeDecodeError:continue
 if pw in s:leaks.append(f.relative_to(P).as_posix())
 if f.suffix=='.py':
  try:ast.parse(s)
  except SyntaxError as e:syntax.append({'path':str(f),'error':str(e)})
 if f.suffix=='.md':
  for link in re.findall(r'\]\(([^)]+)\)',s):
   if link.startswith(('http','#','mailto')):continue
   target=link.split('#')[0].strip('<>')
   if target and not (f.parent/target).exists():broken.append({'file':f.name,'target':target})
ps="ConvertTo-Json -InputObject @(Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -ge 8810 -and $_.LocalPort -le 8830 } | Select-Object LocalAddress,LocalPort,OwningProcess) -Compress"
q=subprocess.run(['powershell','-NoProfile','-Command',ps],capture_output=True,text=True);http=json.loads(q.stdout)
d=subprocess.run(['wsl.exe','--','docker','ps','--format','{{.Names}} {{.ID}} {{.Ports}}'],capture_output=True,text=True);containers=d.stdout.splitlines();entry=json.loads((P/'stands-entry.json').read_text());foreign_http=[f for f in entry['http'] if 8810<=f['LocalPort']<=8830]
preserved_http=all(any(y==f for y in http) for f in foreign_http);preserved_docker=all(f in containers for f in entry['docker'])
native_syntax=subprocess.run(['C:/Program Files/nodejs/node.exe',str(P/'check-js.cjs'),str(P)],capture_output=True,text=True,encoding='utf-8',errors='replace')
diff=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()
with urllib.request.urlopen('http://localhost:8822/qa/version/',timeout=10) as response:version=json.load(response)
with urllib.request.urlopen('http://localhost:8822/qa/state/',timeout=10) as response:state=json.load(response)
(P/'state-final.json').write_text(json.dumps(state,indent=2,ensure_ascii=False),encoding='utf-8')
runtime_ok=version['testing'] and version['head']==head==x['head'] and version['source_digest']==x['source_digest'] and any(f['LocalPort']==8822 and f['OwningProcess']==32520 for f in http)
runtime={'http':'http://localhost:8822','pid':32520,'version':version,'source_evidence':'Startup run.py source guard + no autoreloader + current source manifest + listener PID. /qa/version echoes manifest, not independent attestation.','postgres':'17.11','container':'kidsmap-module09-20261010-r1','container_id':'7c0a77891bf7446cd54ab31b798868912e2f5f2ad4d7721edddc17c92481ea37','volume':'1b432792876a4e921aed8bd0085fd6eae420adcc2579696f67b94dfcc0c8f5b3','browser':'Chromium153.0.8010.12 / module09-r1 / headless shell1243','runtime_match':runtime_ok}
(P/'runtime-final.json').write_text(json.dumps(runtime,indent=2),encoding='utf-8')
broken=[]
for f in P.rglob('*.md'):
 for link in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
  if link.startswith(('http','#','mailto')):continue
  target=link.split('#')[0].strip('<>')
  if target=='verification.json':continue  # This artifact is written below on successful completion.
  if target and not (f.parent/target).exists():broken.append({'file':f.name,'target':target})
for filename in ['runtime-final.json','state-final.json']:
 if pw in (P/filename).read_text(encoding='utf-8'):leaks.append(filename)
summary={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_files':len(source),'source_unchanged':source==x['source_files'],'source_digest':hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),'foreign_files_checked':len(prior)-1,'foreign_drift':drift,'journal_only_row09':journal_ok,'journal_changed_lines':changed,'active_run_unchanged':h(R/'docs/task33/implementation-status.md')==prior['docs/task33/implementation-status.md'],'foreign_http_preserved':preserved_http,'foreign_docker_preserved':preserved_docker,'http_final':http,'docker_final':containers,'known_credential_leaks':leaks,'python_ast_errors':syntax,'js_syntax_exit':native_syntax.returncode,'broken_report_links':broken,'git_diff_check_exit':diff.returncode}
summary.update(head=head,branch=branch,runtime_match=runtime_ok)
ok=summary['source_unchanged'] and not drift and journal_ok and preserved_http and preserved_docker and not leaks and not syntax and not broken and native_syntax.returncode==0 and diff.returncode==0 and runtime_ok and branch==x['branch']
summary['status']='PASS' if ok else 'FAIL';(P/'verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in summary.items() if k not in ['http_final','docker_final']}));sys.exit(0 if ok else 1)
