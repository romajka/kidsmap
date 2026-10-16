import hashlib,json,subprocess,time,urllib.request
from pathlib import Path
h=Path(__file__).resolve().parent;r=h.parents[2];s=r/'.tmp'/h.name;cfg=json.loads((s/'config.json').read_text());py=str(s/'venv/bin/python')
assert(h/'entry.json').exists()
def run(name,args):
 t=time.monotonic();p=subprocess.run(args,cwd=r,capture_output=True,text=True);(h/(name+'.txt')).write_text(p.stdout+p.stderr)
 with(h/'commands.jsonl').open('a')as f:f.write(json.dumps({'name':name,'argv':args,'exit':p.returncode,'seconds':round(time.monotonic()-t,3)})+'\n')
 assert p.returncode==0,(name,p.returncode)
run('locales-build',[py,'scripts/build_isolated_locales.py','build','--output',str(s/'locales'),'--locales','ru','az','en','--compiler','native']);run('locales-verify',[py,'scripts/build_isolated_locales.py','verify','--manifest',str(s/'locales/manifest.json')]);(h/'locale-manifest.json').write_bytes((s/'locales/manifest.json').read_bytes())
paths=json.loads((h/'source-paths.json').read_text());(h/'runtime-source-baseline.json').write_text(json.dumps({n:hashlib.sha256((r/n).read_bytes()).hexdigest()for n in paths},indent=2))
run('runtime-info',[py,str(h/'runtime.py'),'runtime-info'])
a=[py,str(h/'runtime.py'),'serve']
with(s/'server.log').open('wb')as log:p=subprocess.Popen(a,cwd=r,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
meta={'pid':p.pid,'argv':a,'url':f"http://127.0.0.1:{cfg['http_port']}",'container':cfg['container'],'pg_port':cfg['pg_port']};(h/'server.json').write_text(json.dumps(meta,indent=2))
for _ in range(300):
 try:
  source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=1))
  if source['pid']==p.pid:break
 except Exception:pass
 time.sleep(.1)
else:raise RuntimeError('Own HTTP not ready')
assert source['startup_matches_disk'];(h/'runtime-source-red.json').write_text(json.dumps(source,indent=2));(h/'domain-before.json').write_text(json.dumps(json.load(urllib.request.urlopen(meta['url']+'/qa/state/',timeout=5)),indent=2));print(json.dumps({'pid':p.pid,'source_files':len(source['source']),'http_port':cfg['http_port']}))
