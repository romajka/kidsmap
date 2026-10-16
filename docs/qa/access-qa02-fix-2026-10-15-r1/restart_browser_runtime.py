import hashlib,json,os,signal,subprocess,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
s=json.loads((H/'server.json').read_text());p=Path('/proc')/str(s['pid']);assert[x.decode()for x in(p/'cmdline').read_bytes().split(b'\0')if x]==s['argv']and(p/'cwd').resolve()==R
v=json.loads((H/'runtime-source-baseline.json').read_text());assert all(hashlib.sha256((R/f).read_bytes()).hexdigest()==d for f,d in v.items());(H/'server-before-browser.json').write_bytes((H/'server.json').read_bytes());os.kill(s['pid'],signal.SIGTERM)
for _ in range(100):
 if not p.exists()or') Z 'in(p/'stat').read_text():break
 time.sleep(.05)
else:raise AssertionError('Own old HTTP did not stop')
with(S/'server-browser.log').open('wb')as log:child=subprocess.Popen(s['argv'],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
s['pid']=child.pid;(H/'server.json').write_text(json.dumps(s,indent=2))
for _ in range(600):
 try:
  d=json.load(urllib.request.urlopen(s['url']+'/qa/source/',timeout=1))
  if d['pid']==child.pid:break
 except Exception:pass
 time.sleep(.1)
else:raise AssertionError('Own browser runtime not ready')
assert d['startup_matches_disk'];(H/'runtime-source-browser.json').write_text(json.dumps(d,indent=2));(H/'qa-profile-source.json').write_text(json.dumps({f:hashlib.sha256((H/f).read_bytes()).hexdigest()for f in ('runtime.py','settings.py','qa_urls.py','qa_browser.py')},indent=2))
with(H/'commands.jsonl').open('a')as out:out.write(json.dumps({'name':'restart-own-browser-runtime','argv':s['argv'],'old_pid':json.loads((H/'server-before-browser.json').read_text())['pid'],'new_pid':child.pid,'exit':0,'foreign_signals':0})+'\n')
print(json.dumps({'pid':child.pid,'source_match':True}))
