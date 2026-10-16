import hashlib,json,socket,subprocess,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;s=json.loads((H/'server.json').read_text());assert not Path('/proc',str(s['pid'])).exists()
v=json.loads((H/'runtime-source-baseline.json').read_text());assert all(hashlib.sha256((R/f).read_bytes()).hexdigest()==d for f,d in v.items())
with socket.socket()as sock:sock.bind(('127.0.0.1',int(s['url'].rsplit(':',1)[1])))
(H/'server-before-interruption-r3.json').write_bytes((H/'server.json').read_bytes())
with(S/'server-resume-r3.log').open('wb')as log:p=subprocess.Popen(s['argv'],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
s['pid']=p.pid;(H/'server.json').write_text(json.dumps(s,indent=2))
for _ in range(600):
 try:
  d=json.load(urllib.request.urlopen(s['url']+'/qa/source/',timeout=1))
  if d['pid']==p.pid:break
 except Exception:pass
 time.sleep(.1)
else:raise AssertionError('Owned resume not ready')
assert d['startup_matches_disk'];(H/'runtime-source-resume-r3.json').write_text(json.dumps(d,indent=2))
with(H/'commands.jsonl').open('a')as f:f.write(json.dumps({'name':'resume-own-after-interruption-r3','argv':s['argv'],'new_pid':p.pid,'exit':0,'no_reseed_or_migrate':True,'foreign_signals':0})+'\n')
print(json.dumps({'pid':p.pid,'source_match':True}))
