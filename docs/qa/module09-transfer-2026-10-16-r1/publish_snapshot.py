"""Push immutable WIP transfer in bounded packs; shared checkout/index untouched."""
import hashlib,json,os,subprocess,time
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;entry=json.loads((H/'entry.json').read_text());frozen=json.loads((S/'full-tree.json').read_text());ref='refs/heads/'+entry['target_branch'];env=dict(os.environ,GIT_INDEX_FILE=str(S/'publish.index'),GIT_SSH_COMMAND='ssh -o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=60 -o ServerAliveCountMax=10')
def git(*a,input=None):return subprocess.run(['git','-c','gc.auto=0',*a],cwd=R,env=env,input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
statefile=S/'publication-state.json'
if statefile.exists():state=json.loads(statefile.read_text())
else:
 assert not git('ls-remote','origin',ref).strip(),'Target remote branch already exists; do not overwrite'
 local=subprocess.run(['git','show-ref','--verify','--quiet',ref],cwd=R);assert local.returncode==1,'Local target branch exists'
 fullenv=dict(env,GIT_INDEX_FILE=str(S/'full.index'));rows=subprocess.check_output(['git','ls-files','--stage','-z'],cwd=R,env=fullenv);entries={}
 for row in rows.split(b'\0'):
  if not row:continue
  m,n=row.split(b'\t',1);mode,oid,stage=m.split();assert stage==b'0';entries[n.decode()]={'mode':mode.decode(),'oid':oid.decode()}
 changed=[n for n in subprocess.check_output(['git','diff','--cached','--name-only','-z',entry['head']],cwd=R,env=fullenv).decode().split('\0')if n]
 sizes={m['path']:m['bytes']for m in json.loads((H/'transfer-files.json').read_text())};images=[];code=[]
 for n in changed:
  (images if Path(n).suffix.lower()in{'.png','.jpg','.jpeg','.webp','.gif','.pdf','.zip'}and n in entries else code).append(n)
 groups=[code];chunk=[];size=0
 for n in sorted(images):
  s=sizes.get(n,(R/n).stat().st_size)
  if chunk and size+s>450*1024**2:groups.append(chunk);chunk=[];size=0
  chunk.append(n);size+=s
 if chunk:groups.append(chunk)
 git('read-tree',entry['head']);parent=entry['head'];commits=[]
 for i,names in enumerate(groups):
  payload=b''
  for n in names:
   m=entries.get(n);payload+=((m['mode']+' '+m['oid'])if m else'0 '+'0'*40).encode()+b'\t'+n.encode()+b'\0'
  git('update-index','-z','--index-info',input=payload);tree=git('write-tree').decode().strip();msg='Preserve accumulated KidsMap source and module09 handoff'if i==0 else f'Preserve module QA images ({i}/{len(groups)-1})'
  commit=git('-c','commit.gpgsign=false','commit-tree',tree,'-p',parent,input=(msg+'\n\nWIP transfer only; no module09 full acceptance or deployment.\n').encode()).decode().strip();commits.append({'index':i,'commit':commit,'tree':tree,'paths':len(names),'message':msg,'pushed':False});parent=commit
 assert tree==frozen['tree'],'Final split commit tree differs from frozen payload'
 state={'ref':ref,'base':entry['head'],'tree':tree,'commits':commits};statefile.write_text(json.dumps(state,indent=2))
 print(json.dumps({'commits_prepared':len(commits),'paths':len(changed),'final_payload_commit':parent}),flush=True)
for c in state['commits']:
 if c['pushed']:continue
 remote=git('ls-remote','origin',ref).decode().split();remote_sha=remote[0]if remote else None
 if remote_sha!=c['commit']:
  allowed={entry['head']}|{x['commit']for x in state['commits']if x['index']<c['index']}
  assert remote_sha is None or remote_sha in allowed,remote_sha
  print(json.dumps({'pushing':c['index']+1,'of':len(state['commits']),'commit':c['commit'],'paths':c['paths']}),flush=True)
  log=S/f'push-{c["index"]}.log'
  with log.open('ab')as f:result=subprocess.run(['git','-c','gc.auto=0','-c','pack.threads=2','-c','pack.windowMemory=32m','-c','pack.window=3','push','--progress','origin',c['commit']+':'+ref],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT)
  assert result.returncode==0,{'push_exit':result.returncode,'log':str(log)}
  remote=git('ls-remote','origin',ref).decode().split();assert remote and remote[0]==c['commit']
 current=subprocess.run(['git','rev-parse','--verify',ref],cwd=R,capture_output=True,text=True);old=current.stdout.strip()if current.returncode==0 else'0'*40;git('update-ref',ref,c['commit'],old)
 c['pushed']=True;statefile.write_text(json.dumps(state,indent=2));print(json.dumps({'verified_remote':c['commit'],'step':c['index']+1}),flush=True)
main=git('ls-remote','origin','refs/heads/main').decode().split()[0];assert main==entry['origin_main'],'Remote main changed externally; inspect before asserting unchanged'
assert git('rev-parse','HEAD').decode().strip()==entry['head'];assert hashlib.sha256((R/'.git/index').read_bytes()).hexdigest()==entry['index_sha256']
record={'branch':entry['target_branch'],'remote_payload_commit':state['commits'][-1]['commit'],'frozen_tree':state['tree'],'pushed_commits':state['commits'],'remote_main_before':entry['origin_main'],'remote_main_after':main,'remote_main_unchanged':True,'shared_HEAD_index_preserved':True,'no_deployment':True,'full_module09_tests':'NOT RUN','not_transferred':'runtime credentials/.env/localDB/new ignored .tmp/cache/private-media/pyc'}
(H/'publication.json').write_text(json.dumps(record,ensure_ascii=False,indent=2));print(json.dumps({'payload_published':record['remote_payload_commit'],'main_unchanged':True,'HEAD_index_preserved':True}),flush=True)
