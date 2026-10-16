"""Freeze transfer in an alternate Git index, scan blobs without printing secrets."""
import ast,hashlib,json,os,re,subprocess,time
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;entry=json.loads((H/'entry.json').read_text());env=dict(os.environ,GIT_INDEX_FILE=str(S/'full.index'))
def git(*a,input=None):return subprocess.run(['git','-c','gc.auto=0',*a],cwd=R,env=env,input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
assert not(S/'full.index').exists();git('read-tree',entry['head']);print('Alternate index initialized',flush=True)
git('-c','core.compression=1','add','-A','--','.');print('Visible source/docs/PNG frozen',flush=True)
logs=[n for n in git('ls-files','--others','--ignored','--exclude-standard','-z','docs/qa').decode().split('\0')if n.endswith('.log')]
if logs:git('add','-f','--',*logs)
print(json.dumps({'additional_QA_logs':len(logs)}),flush=True)
changed=[n for n in git('diff','--cached','--name-only','-z',entry['head']).decode().split('\0')if n];all_entries={}
for row in git('ls-files','--stage','-z').split(b'\0'):
 if not row:continue
 meta,path=row.split(b'\t',1);mode,oid,stage=meta.split();assert stage==b'0';all_entries[path.decode()]={'mode':mode.decode(),'oid':oid.decode()}
known=set()
for pattern in ('*/credentials.json','*/secrets.json','*/secret.json'):
 for p in(R/'.tmp').glob(pattern):
  try:d=json.loads(p.read_text())
  except(ValueError,OSError):continue
  if isinstance(d,dict):
   for k,v in d.items():
    if re.search('password|secret|token|api.?key',k,re.I)and isinstance(v,str)and len(v)>=16:known.add(v.encode())
secret_re=re.compile(b'|'.join(re.escape(x)for x in sorted(known,key=len,reverse=True)))if known else None
hard=[('private_key',re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\r\n]')),('github_token',re.compile(rb'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b')),('github_fine_token',re.compile(rb'github_pat_[A-Za-z0-9_]{60,}')),('aws_access_id',re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b')),('google_api_key',re.compile(rb'AIza[0-9A-Za-z_-]{35}'))]
forbidden=[];leaks=[];syntax=[];py_count=0;text_count=0;total=0;largest=[];manifest=[];sources={}
proc=subprocess.Popen(['git','cat-file','--batch'],cwd=R,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
def blob(oid):
 proc.stdin.write((oid+'\n').encode());proc.stdin.flush();head=proc.stdout.readline().split();assert head[1]==b'blob';n=int(head[2]);data=proc.stdout.read(n);assert proc.stdout.read(1)==b'\n';return data
for i,n in enumerate(changed):
 if n not in all_entries:continue
 m=all_entries[n];suffix=Path(n).suffix.lower()
 if re.search(r'(^|/)(\.env($|\.)|credentials[^/]*|id_rsa|id_ed25519|[^/]*\.(?:sqlite3?|db|dump|pem|key|p12))$',n,re.I)and n!='.env.example':forbidden.append(n)
 data=blob(m['oid']);total+=len(data);manifest.append({'path':n,**m,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 if len(data)>90*1024**2:largest.append(n)
 if n.startswith(('src/','static/','locale/','config/','templates/')):sources[n]=hashlib.sha256(data).hexdigest()
 if suffix in('.py','.js','.cjs','.mjs','.html','.css','.po','.txt','.json','.jsonl','.md','.diff','.patch','.log','.csv','.yml','.yaml','.sh','.candidate','.template',''):
  text_count+=1
  if secret_re and secret_re.search(data):leaks.append({'path':n,'kind':'known_local_QA_secret'})
  for label,pattern in hard:
   if pattern.search(data):leaks.append({'path':n,'kind':label})
  if suffix=='.py'and n.startswith(('src/','scripts/','config/')):
   py_count+=1
   try:ast.parse(data,filename=n)
   except(SyntaxError,ValueError)as exc:syntax.append({'path':n,'line':getattr(exc,'lineno',None),'kind':type(exc).__name__})
 if i%2000==0:print(json.dumps({'scanned':i,'total':len(changed)}),flush=True)
proc.stdin.close();proc.wait();assert proc.returncode==0
(H/'transfer-files.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(H/'transferred-source-manifest.json').write_text(json.dumps(sources,indent=2))
report={'scope':'Frozen alternate index; all nonignored changes plus safe QA logs pending scan','files_changed_or_added':len(changed),'added_QA_logs':logs,'payload_MiB':round(total/1024**2,2),'text_files_scanned':text_count,'known_QA_secret_values_compared':len(known),'forbidden_paths':forbidden,'secret_findings':leaks,'large_files_over_90MiB':largest,'application_python_ast':{'files':py_count,'errors':syntax},'full_tests':'NOT RUN; transfer only','shared_index_match':hashlib.sha256((R/'.git/index').read_bytes()).hexdigest()==entry['index_sha256'],'HEAD_match':git('rev-parse','HEAD').decode().strip()==entry['head'],'target_branch':entry['target_branch'],'deploy_trigger':'main only; target branch does not match','next_scope':'SOCIAL03 fresh PLAN/recheck; implementation approval PENDING'}
(H/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items()if k not in('added_QA_logs',)},ensure_ascii=False),flush=True)
(S/'snapshot-index-state.json').write_text(json.dumps({'changed_paths':changed,'entry_count':len(all_entries),'entries':all_entries},indent=2))
if forbidden or leaks or largest:raise SystemExit('Publication guard found paths/content; inspect finding metadata, no publication yet')
