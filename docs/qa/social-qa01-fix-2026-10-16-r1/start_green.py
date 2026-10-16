"""Own approved-fix stand only; fresh DB initial seed, no shared state."""
import json,subprocess,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;cfg=json.loads((S/'config.json').read_text());py=str(R/'.venv/bin/python')
def run(name,args):
 p=subprocess.run(['python3',str(H/'run_command.py'),name,*args],cwd=R);assert p.returncode==0,(name,p.returncode)
run('locales-verify',[py,'scripts/build_isolated_locales.py','verify','--manifest',str(S/'locales/manifest.json')]);(H/'locale-manifest.json').write_bytes((S/'locales/manifest.json').read_bytes())
run('prepare',[py,str(H/'runtime.py'),'prepare']);run('runtime-info',[py,str(H/'runtime.py'),'runtime-info'])
a=[py,str(H/'runtime.py'),'serve']
with(S/'server.log').open('wb')as log:p=subprocess.Popen(a,cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
meta={'pid':p.pid,'argv':a,'url':f"http://127.0.0.1:{cfg['http_port']}",'container':cfg['container'],'pg_port':cfg['pg_port']};(H/'server.json').write_text(json.dumps(meta,indent=2))
for _ in range(100):
 try:
  source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=2));assert source['pid']==p.pid and source['startup_matches_disk'];break
 except Exception:time.sleep(.2)
else:raise RuntimeError('Own HTTP not ready')
(H/'runtime-source-start.json').write_text(json.dumps(source,indent=2));print(json.dumps({'pid':p.pid,'source':len(source['source']),'http_port':cfg['http_port']}))
