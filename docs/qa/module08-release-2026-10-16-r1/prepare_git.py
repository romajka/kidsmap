"""Create reviewed release commits with a private index; never change original HEAD/index/worktree."""
from pathlib import Path
import hashlib,json,os,subprocess,re,time
r=Path.cwd();h=r/'docs/qa/module08-release-2026-10-16-r1';s=r/'.tmp/module08-release-2026-10-16-r1'
accept=json.loads((r/'docs/qa/module08-accept-2026-10-16-r2/verification.json').read_text());assert accept['status']=='LOCAL PASS'
base=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert base=='e4e05cc213b34e2d771ecb854901bfd016d1db51'
branch='codex/module08-release-2026-10-16';assert subprocess.run(['git','show-ref','--verify','--quiet','refs/heads/'+branch]).returncode==1
original_index=r/'.git/index';index_before=hashlib.sha256(original_index.read_bytes()).hexdigest()
paths=sorted(set(n for n in subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z']).decode().split('\0')if n))
secrets=set()
for p in(r/'.tmp').glob('*/credentials.json'):
 try:
  for k,v in json.loads(p.read_text()).items():
   if isinstance(v,str)and len(v)>=12 and any(x in k for x in ['password','secret','token','key']):secrets.add(v)
 except(ValueError,OSError):pass
exclude=[];selected=[]
binary={'.png','.jpg','.jpeg','.gif','.webp','.pdf','.zip','.mo','.woff','.woff2','.ttf','.ico'}
for n in paths:
 p=r/n;assert p.is_file(),n;reasons=[]
 if p.suffix.lower()not in binary:
  try:t=p.read_text()
  except UnicodeDecodeError:t=''
  if any(v in t for v in secrets):reasons.append('owned QA credential value')
  if p.name.startswith('.env')and p.name!='.env.example':reasons.append('environment file')
  if re.search(r'-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----[\s\S]{100,}?-----END',t):reasons.append('private key block')
  if n.startswith('docs/qa/')and re.search(r'name="csrfmiddlewaretoken" value="[A-Za-z0-9]{32,}"',t.replace('\\"','"')):reasons.append('raw historical QA CSRF token')
 if reasons:exclude.append({'path':n,'reasons':reasons});assert n.startswith('docs/qa/'),'Sensitive application source needs review'
 else:selected.append(n)
assert len(exclude)==5,exclude
meta={'branch':branch,'base':base,'selected_count':len(selected),'excluded':exclude,'known_QA_secrets_checked':len(secrets),'original_files_preserved':True,'private_index':True,'binary_chunk_limit_bytes':450*1024**2,'deploy_scope':'all current application changes modules01–08; no module09 work','application_ref':'first code/text commit; later commits QA binaries only'}
(h/'git-package-plan.json').write_text(json.dumps(meta,indent=2))
selected.append(str((h/'git-package-plan.json').relative_to(r)))
selected=sorted(set(selected))
frozen={n:hashlib.sha256((r/n).read_bytes()).hexdigest()for n in selected}
(s/'frozen-paths.json').write_text(json.dumps(frozen,indent=2))
core=[n for n in selected if not(n.startswith('docs/qa/')and Path(n).suffix.lower()in binary)]
bins=[n for n in selected if n not in core]
groups=[core];chunk=[];size=0
for n in bins:
 z=(r/n).stat().st_size
 if chunk and size+z>450*1024**2:groups.append(chunk);chunk=[];size=0
 chunk.append(n);size+=z
if chunk:groups.append(chunk)
env={**os.environ,'GIT_INDEX_FILE':str(s/'release.index')}
def git(*args,input=None):
 p=subprocess.run(['git',*args],cwd=r,env=env,input=input,capture_output=True)
 if p.returncode:raise RuntimeError((args,p.stderr.decode()[:500]))
 return p.stdout.decode().strip()
git('read-tree',base)
parent=base;commits=[]
for i,group in enumerate(groups):
 assert all(hashlib.sha256((r/n).read_bytes()).hexdigest()==frozen[n]for n in group),'Frozen file drift'
 pathfile=s/f'paths-{i}.nul';pathfile.write_bytes(b'\0'.join(n.encode()for n in group)+b'\0')
 git('add','--pathspec-from-file='+str(pathfile),'--pathspec-file-nul')
 tree=git('write-tree')
 message='Apply reviewed KidsMap modules01–08 fixes and local acceptance'if i==0 else'Preserve module QA browser evidence batch '+str(i)
 commit=git('commit-tree',tree,'-p',parent,input=(message+'\n').encode())
 git('update-ref','refs/heads/'+branch,commit,('0'*40 if i==0 else parent))
 commits.append({'part':i,'commit':commit,'tree':tree,'files':len(group),'bytes':sum((r/n).stat().st_size for n in group),'message':message})
 parent=commit
 (s/'git-commits-progress.json').write_text(json.dumps({'base':base,'branch':branch,'commits':commits},indent=2))
 print(json.dumps({'committed_part':i,'commit':commit,'files':len(group),'MB':round(commits[-1]['bytes']/1024**2,1)}),flush=True)
assert hashlib.sha256(original_index.read_bytes()).hexdigest()==index_before
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==base
assert all(hashlib.sha256((r/n).read_bytes()).hexdigest()==v for n,v in frozen.items())
result={'branch':branch,'base':base,'code_commit':commits[0]['commit'],'evidence_commit':commits[-1]['commit'],'commits':commits,'original_HEAD_preserved':True,'original_index_SHA_preserved':index_before,'frozen_files_match':True,'selected_count':len(selected),'excluded':exclude,'push':'NOT RUN'}
(h/'git-commits.json').write_text(json.dumps(result,indent=2));print(json.dumps({'prepared':True,'code_commit':commits[0]['commit'],'evidence_commit':parent,'parts':len(commits)}))
