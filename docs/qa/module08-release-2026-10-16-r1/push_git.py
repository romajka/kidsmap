from pathlib import Path
import json,subprocess,time
r=Path.cwd();h=r/'docs/qa/module08-release-2026-10-16-r1';m=json.loads((h/'git-commits.json').read_text());branch=m['branch'];remote=subprocess.run(['git','ls-remote','--exit-code','origin','refs/heads/'+branch],capture_output=True,text=True);assert remote.returncode==2,('remote branch already exists',remote.returncode)
rows=[]
for row in m['commits']:
 t=time.monotonic();p=subprocess.run(['git','push','origin',row['commit']+':refs/heads/'+branch],cwd=r,capture_output=True,text=True);(h/('push-part'+str(row['part'])+'.txt')).write_text(p.stdout+p.stderr);assert p.returncode==0,('push failed',row['part'],p.returncode)
 actual=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],text=True).split()[0];assert actual==row['commit'];rows.append({'part':row['part'],'commit':actual,'exit':0,'seconds':round(time.monotonic()-t,3)});(h/'push-progress.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows[-1]),flush=True)
(h/'push-verification.json').write_text(json.dumps({'branch':branch,'code_commit':m['code_commit'],'final_commit':m['evidence_commit'],'remote_verified':True,'parts':rows,'force_used':False,'original_HEAD_index_worktree_preserved':True},indent=2))
