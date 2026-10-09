"""Restart this existing synthetic QA stand only, with its sanitized process environment."""
from pathlib import Path
import json,subprocess,urllib.request
S=Path(__file__).resolve().parent;R=S.parents[1];N='kidsmap-place-acceptance-20261009-8792'
env=json.loads((S/'env.json').read_text());assert env['DJANGO_TESTING']=='1'
assert not any(env.get(k)for k in ('DATABASE_URL','LEGACY_DATABASE_URL','REDIS_URL','GOOGLE_APPLICATION_CREDENTIALS'))
x=json.loads((S/'runtime-source.json').read_text())
try:
 with urllib.request.urlopen('http://localhost:8792/qa/acceptance-version/',timeout=3)as f:v=json.load(f)
 assert v['testing']and v['source_digest']==x['source_digest']
 print('Existing isolated stand8792 is already running');raise SystemExit(0)
except OSError:pass
c=json.loads(subprocess.check_output(['docker','inspect',N]))[0]
assert c['Config']['Labels'].get('kidsmap.qa.owner')==N
assert c['HostConfig']['NetworkMode']=='none'and not c['HostConfig']['PortBindings']
if not c['State']['Running']:subprocess.run(['docker','start',N],check=True,stdout=subprocess.DEVNULL)
for i in range(100):
 r=subprocess.run(['docker','exec',N,'pg_isready','-h','/qa-socket','-U','qa_stage04'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 if r.returncode==0:break
 import time;time.sleep(.1)
else:raise RuntimeError('Synthetic QA DB did not become ready')
with(S/'server.log').open('a')as f:p=subprocess.Popen([str(R/'.venv/bin/python'),str(S/'serve.py')],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
(S/'server.pid').write_text(str(p.pid));print('Started existing isolated stand8792; PID',p.pid)
