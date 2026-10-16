import json,os,signal,subprocess,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
meta=json.loads((H/'server.json').read_text());pid=meta['pid'];proc=Path('/proc')/str(pid)
assert [v.decode()for v in(proc/'cmdline').read_bytes().split(b'\0')if v]==meta['argv']
assert (proc/'cwd').resolve()==R and str(H/'runtime.py')==meta['argv'][1]
assert json.load(urllib.request.urlopen(meta['url']+'/qa/source/'))['pid']==pid
(H/'server-before-QA-mail-proof.json').write_text(json.dumps(meta,indent=2));os.kill(pid,signal.SIGTERM)
for _ in range(600):
 if not proc.exists():break
 time.sleep(.1)
else:raise AssertionError('Own process did not stop')
meta['argv'][0]=str(S/'venv/bin/python')
with(S/'server-after-owned-venv.log').open('wb')as log:p=subprocess.Popen(meta['argv'],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
meta['pid']=p.pid;(H/'server.json').write_text(json.dumps(meta,indent=2))
for _ in range(600):
 try:
  data=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=1))
  if data['pid']==p.pid:break
 except Exception:pass
 time.sleep(.1)
else:raise AssertionError('Own source not ready')
(H/'runtime-source-with-loaded-MO.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));print(json.dumps({'old_own_pid':pid,'new_own_pid':p.pid,'application_source_matches':data['startup_matches_disk'],'actual_opened_MO_count':len(data['actual_opened_MO'])}))
