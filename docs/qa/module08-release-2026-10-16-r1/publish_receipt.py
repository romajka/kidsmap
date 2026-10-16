from pathlib import Path
import json,subprocess,hashlib,os,re
r=Path.cwd();h=r/'docs/qa/module08-release-2026-10-16-r1';s=r/'.tmp/module08-release-2026-10-16-r1';m=json.loads((h/'git-commits.json').read_text());parent=m['evidence_commit'];branch=m['branch'];original_index_SHA=m['original_index_SHA_preserved']
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==m['base']
assert hashlib.sha256((r/'.git/index').read_bytes()).hexdigest()==original_index_SHA
assert subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],text=True).split()[0]==parent
meta=json.loads((h/'verification.json').read_text());assert meta['status'].startswith('RELEASED')
secrets=set()
for p in(r/'.tmp').glob('*/credentials.json'):
 try:
  for k,v in json.loads(p.read_text()).items():
   if isinstance(v,str)and len(v)>=12 and any(x in k for x in ['password','secret','token','key']):secrets.add(v)
 except(ValueError,OSError):pass
names=sorted(str(p.relative_to(r))for p in h.rglob('*')if p.is_file()and subprocess.run(['git','check-ignore','-q',str(p.relative_to(r))]).returncode!=0)
names.append('docs/qa/continuation-and-repair-prompts-2026-10-11.md')
for n in names:
 p=r/n
 if p.suffix=='.png':continue
 t=p.read_text()
 assert not any(v in t for v in secrets),('Credential value in receipt',n)
 assert not re.search(r'name="csrfmiddlewaretoken" value="[A-Za-z0-9]{32,}"',t.replace('\\"','"')),('CSRF token',n)
env={**os.environ,'GIT_INDEX_FILE':str(s/'release-receipt.index')}
def git(*args,input=None):
 p=subprocess.run(['git',*args],cwd=r,env=env,input=input,capture_output=True)
 assert p.returncode==0,(args,p.returncode,p.stderr.decode()[:300])
 return p.stdout.decode().strip()
git('read-tree',parent)
f=s/'receipt-paths.nul';f.write_bytes(b'\0'.join(n.encode()for n in names)+b'\0');git('add','--pathspec-from-file='+str(f),'--pathspec-file-nul');tree=git('write-tree');commit=git('commit-tree',tree,'-p',parent,input=b'Record verified module08 production rollout and recovery evidence\n')
changed=git('diff','--name-only',m['code_commit'],commit).splitlines();assert changed and all(n.startswith('docs/qa/')for n in changed),'Runtime source changed after tested code commit'
git('update-ref','refs/heads/'+branch,commit,parent);out=git('push','origin',commit+':refs/heads/'+branch);remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],text=True).split()[0];assert remote==commit
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==m['base'];assert hashlib.sha256((r/'.git/index').read_bytes()).hexdigest()==original_index_SHA
result={'branch':branch,'code_commit':m['code_commit'],'QA_commit':parent,'receipt_commit':commit,'remote_verified':True,'later_commits_only_docs_QA':True,'original_HEAD_index_preserved':True,'receipt_files':len(names),'force':False};(s/'publication-final.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
