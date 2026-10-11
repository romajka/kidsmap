"""Artifact/source/foreign-stand integrity verification, read-only except own evidence."""
from pathlib import Path
import ast,json,csv,hashlib,re,subprocess,datetime,urllib.request,collections,sys
from PIL import Image
P=Path(__file__).resolve().parent;R=P.parents[2];checks={}
def read(n):return json.loads((P/n).read_text(encoding='utf-8'))
def save(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def check(n,passed,**detail):checks[n]={'PASS':bool(passed),**detail}
def run(cmd):return subprocess.run(cmd,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace')
prior=read('preservation-entry.json');snap=read('snapshot.json');journal='docs/qa/module-acceptance-prompts.md'
changed=[f for f,h in prior.items()if f!=journal and(not(R/f).is_file()or hashlib.sha256((R/f).read_bytes()).hexdigest()!=h)]
check('foreign_file_preservation',not changed,files=len(prior),allowed_change=journal,changed=changed)
source={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for top in('src','static','config','locale','templates')for p in(R/top).rglob('*')if p.is_file()and'__pycache__'not in p.parts and p.suffix!='.pyc'}
digest=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()
check('source_exact',source==snap['source_files'],files=len(source),digest=digest)
head=run(['git','rev-parse','HEAD']);branch=run(['git','branch','--show-current']);active=next(x.split(':',1)[1].strip()for x in(R/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines()if x.startswith('active_run:'))
check('head_branch_active_run',head.returncode==branch.returncode==0 and head.stdout.strip()==snap['head']and branch.stdout.strip()==snap['branch']and active==snap['active_run'],head=head.stdout.strip(),branch=branch.stdout.strip(),active_run=active)
def outside13(b):return re.sub(rb'^\| 13 \|[^\r\n]*',b'',b,flags=re.M)
old=(P/'journal-entry.txt').read_bytes();now=(R/journal).read_bytes()
check('journal_only_row13',outside13(old)==outside13(now),journal_updated=old!=now,row13=re.search(rb'^\| 13 \|[^\r\n]*',now,re.M).group().decode('utf-8'))
audit_rows=re.findall(rb'^\| (\d{2}) \|[^\r\n]*',now,re.M)
complete_rows=[m.group(1).decode()for m in re.finditer(rb'^\| (\d{2}) \|[^\r\n]*\| DONE[^\r\n]*',now,re.M)]
check('journal_all13_completed',len(audit_rows)==13 and len(complete_rows)==13 and b'DONE' in re.search(rb'^\| 13 \|[^\r\n]*',now,re.M).group(),complete_rows=complete_rows,scope='Audit report completion, not product PASS')
version=json.load(urllib.request.urlopen('http://localhost:8831/qa/version/'));version['verified_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save('runtime-final.json',version)
check('runtime_sources_match',version['testing']and version['entry_matches_startup']and version['startup_matches_disk']and version['current_digest']==digest,pid=version['pid'],django=version['django'],python=version['python'],http_port=8831,postgres_port=55444)
ps="ConvertTo-Json -InputObject @((Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in @(8831,8832,55442,55443,55444,8827,8828,8829,8830) } | Select-Object LocalAddress,LocalPort,OwningProcess)) -Compress"
listeners=run(['powershell','-NoProfile','-Command',ps]);docker=run(['wsl.exe','--','docker','ps','--format','{{.Names}} {{.ID}} {{.Ports}}']);mounts=run(['wsl.exe','--','docker','inspect','--format','{{json .Mounts}}','kidsmap-module13-20261011-r1']);ids=run(['wsl.exe','--','docker','inspect','--format','{{.Name}} {{.Id}}','kidsmap-module11-20261011-r1','kidsmap-module12-20261011-r1','kidsmap-module13-20261011-r1'])
stands={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'http':json.loads(listeners.stdout),'docker':docker.stdout.splitlines(),'container_ids':ids.stdout.splitlines(),'own_mounts':json.loads(mounts.stdout),'exit_codes':{'http':listeners.returncode,'docker':docker.returncode,'mounts':mounts.returncode,'ids':ids.returncode},'own_sessions':{'http':82042,'browser':'module13-r1','delegated_browser':'module13-visual'},'root_browser_pid':22052,'foreign_stands_not_stopped':True};save('stands-final.json',stands)
entry=read('stands-entry.json');same=all(any(y['LocalPort']==x['LocalPort']and y['OwningProcess']==x['OwningProcess']for y in stands['http'])for x in entry['http'])and all(x in stands['docker']for x in entry['docker'])
check('foreign_stands_preserved',same and all(x==0 for x in stands['exit_codes'].values()),foreign_listeners=len(entry['http']),foreign_containers=len(entry['docker']))
files=list(P.rglob('*.json'));invalid=[]
for f in files:
 try:json.loads(f.read_text(encoding='utf-8'))
 except Exception as e:invalid.append({'file':f.relative_to(P).as_posix(),'error':type(e).__name__})
check('json_parse',not invalid,files=len(files),invalid=invalid)
py=list(P.rglob('*.py'));invalid=[]
for f in py:
 try:ast.parse(f.read_text(encoding='utf-8'))
 except Exception as e:invalid.append({'file':f.relative_to(P).as_posix(),'error':type(e).__name__})
check('qa_python_ast',not invalid,files=len(py),invalid=invalid)
manifest=[];invalid=[]
for f in sorted(P.rglob('*.png')):
 try:
  with Image.open(f)as im:width,height=im.size;im.verify()
  manifest.append({'path':f.relative_to(P).as_posix(),'width':width,'height':height,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'kind':'DERIVED contact sheet'if f.name.startswith('contact-')else'native PNG; see role/attempt manifest for completed-run status'})
 except Exception as e:invalid.append({'file':f.relative_to(P).as_posix(),'error':type(e).__name__})
save('screenshots-manifest.json',{'all_retained_png':len(manifest),'derived_contact_sheets':sum(x['kind'].startswith('DERIVED')for x in manifest),'root_png':sum(not x['path'].startswith('browser-review/')for x in manifest),'screenshots':manifest})
check('png_integrity',not invalid,files=len(manifest),invalid=invalid)
matrix=read('matrix.json');counts=read('counts.json');c=collections.Counter(x['status']for x in matrix['rows']);fresh=read('fresh-findings.json');check('fresh_counts',dict(c)==counts['combined_browser_assertions']and fresh['confirmed_ids']==10 and fresh['distinct_causes']==9,browser_assertions=dict(c),fresh_ids=fresh['confirmed_ids'],fresh_causes=fresh['distinct_causes'])
missing=[]
for x in matrix['rows']:
 for key in ['evidence_result','screenshot','shot']:
  if x.get(key)and not(P/x[key]).is_file():missing.append(x[key])
check('matrix_evidence_exists',not missing,missing=sorted(set(missing)))
links=[]
for f in P.rglob('*.md'):
 for target in re.findall(r'\[[^\]]*\]\(([^\)]+)\)',f.read_text(encoding='utf-8')):
  target=target.strip('<>');target=target.split('#')[0]
  if not target or re.match(r'^(https?://|mailto:|codex:|app:)',target):continue
  target=re.sub(r':\d+$','',target)
  if not(f.parent/target).exists():links.append({'file':f.relative_to(P).as_posix(),'target':target})
check('markdown_links',not links,missing=links)
for folder in['source-review','reconciliation','test-review','browser-review']:
 result=read(folder+'/verification.json');check(folder+'_verifier',result.get('exit_code')==0 or result.get('exit_code')is None and all(v.get('PASS',v)for v in result.get('checks',{}).values()),record=folder+'/verification.json')
text=(P/'REPORT.md').read_text(encoding='utf-8');check('nine_report_sections',len(re.findall(r'^## [1-9]\. ',text,re.M))==9)
credential=(R/'.tmp/module13-20261011-r1/credential').read_bytes();found=[]
for f in P.rglob('*'):
 if f.is_file()and f.suffix!='.png'and credential in f.read_bytes():found.append(f.relative_to(P).as_posix())
check('local_credential_absent',not found,found=found)
diff=run(['git','diff','--check']);check('git_diff_check',diff.returncode==0,exit_code=diff.returncode,output=diff.stdout+diff.stderr)
save('preservation-final.json',{'checked_foreign_files':len(prior),'changed_except_journal':changed,'source_digest':digest,'source_files':len(source),'head':head.stdout.strip(),'branch':branch.stdout.strip(),'active_run':active,'journal_other_bytes_unchanged':outside13(old)==outside13(now),'current_worktree':run(['git','status','--short']).stdout.splitlines()})
status=0 if all(x['PASS']for x in checks.values())else 1
save('verification.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':'.venv/Scripts/python.exe -X utf8 docs/qa/module13-2026-10-11-r1/verify-final.py','exit_code':status,'checks':checks,'scope':'Evidence/source/preservation integrity only. Product/backend outcome remains FAIL with explicit NOT RUN.'})
print(json.dumps({'checks':len(checks),'PASS':sum(x['PASS']for x in checks.values()),'failures':{k:v for k,v in checks.items()if not v['PASS']},'exit_code':status,'png':len(manifest)},ensure_ascii=False));sys.exit(status)
