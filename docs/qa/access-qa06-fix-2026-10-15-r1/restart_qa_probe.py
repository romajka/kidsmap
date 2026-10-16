import json,os,signal,subprocess,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
meta=json.loads((H/'server.json').read_text());proc=Path('/proc')/str(meta['pid']);args=[x.decode()for x in(proc/'cmdline').read_bytes().split(b'\0')if x];assert args==meta['argv']and(proc/'cwd').resolve()==R
p=H/'qa_urls.py';text=p.read_text();text=text.replace('from qa_evidence import mail,state','from qa_evidence import mail,state\nfrom status_probe import status_urls');text=text.replace("urlpatterns=[path('qa/source/',source)","urlpatterns=[path('qa/status-probe/',status_urls),path('qa/source/',source)");p.write_text(text)
(H/'server-before-readonly-probe.json').write_text(json.dumps(meta,indent=2));os.kill(meta['pid'],signal.SIGTERM)
for _ in range(100):
 try:
  if(proc/'stat').read_text().split()[2]=='Z':break
 except FileNotFoundError:break
 time.sleep(.05)
else:raise RuntimeError('Own HTTP did not stop')
with(S/'server-status-probe.log').open('wb')as log:p=subprocess.Popen(meta['argv'],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
meta['pid']=p.pid;(H/'server.json').write_text(json.dumps(meta,indent=2))
for _ in range(100):
 try:
  source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=1))
  if source['pid']==p.pid:break
 except Exception:pass
 time.sleep(.1)
else:raise RuntimeError('Own HTTP startup failed')
assert source['typed_confirmation_strip']is False and source['startup_matches_disk'];print(json.dumps({'own_pid':p.pid,'new_route':'read-only own status probe','application_changes':[]}))
