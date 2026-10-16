"""Restart only this run's precisely identified HTTP process after approved source changes."""
import hashlib,json,os,signal,socket,subprocess,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;s=json.loads((H/'server.json').read_text());p=Path('/proc')/str(s['pid']);assert[x.decode()for x in(p/'cmdline').read_bytes().split(b'\0')if x]==s['argv']and(p/'cwd').resolve()==R
old=json.loads((H/'runtime-source-baseline.json').read_text());delta=[f for f,v in old.items()if hashlib.sha256((R/f).read_bytes()).hexdigest()!=v];assert set(delta)<=set(['src/catalog/controllers/workflow_notifications.py','src/catalog/templates/pages/account_notifications.html','src/catalog/urls.py'])
(H/'runtime-source-baseline-before-patch.json').write_text(json.dumps(old,indent=2));(H/'server-before-patch.json').write_bytes((H/'server.json').read_bytes())
for f in delta:
 data=subprocess.check_output(['git','show','HEAD:'+f],cwd=R);assert hashlib.sha256(data).hexdigest()==old[f];(H/('before-'+Path(f).name)).write_bytes(data)
new={f:hashlib.sha256((R/f).read_bytes()).hexdigest()for f in old};(H/'runtime-source-baseline.json').write_text(json.dumps(new,indent=2))
os.kill(s['pid'],signal.SIGTERM)
for _ in range(100):
 if not p.exists()or') Z 'in(p/'stat').read_text():break
 time.sleep(.05)
else:raise AssertionError('Own old HTTP did not exit')
with(S/'server-patched.log').open('wb')as log:newproc=subprocess.Popen(s['argv'],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
s['pid']=newproc.pid;(H/'server.json').write_text(json.dumps(s,indent=2))
for _ in range(600):
 try:
  d=json.load(urllib.request.urlopen(s['url']+'/qa/source/',timeout=1))
  if d['pid']==newproc.pid:break
 except Exception:pass
 time.sleep(.1)
else:raise AssertionError('New owned source not ready')
assert d['startup_matches_disk'];(H/'runtime-source-patched.json').write_text(json.dumps(d,indent=2))
with(H/'commands.jsonl').open('a')as f:f.write(json.dumps({'name':'restart-own-approved-patch','argv':s['argv'],'old_pid':json.loads((H/'server-before-patch.json').read_text())['pid'],'new_pid':newproc.pid,'identity_checked':True,'delta':delta,'exit':0})+'\n')
print(json.dumps({'source_match':True,'pid':newproc.pid,'delta':delta}))
