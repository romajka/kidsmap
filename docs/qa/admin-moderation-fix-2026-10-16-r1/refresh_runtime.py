"""Refresh only this run's isolated source/runtime after workers finish."""
import hashlib,json,os,signal,subprocess,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;source=S/'source'
cfg=json.loads((S/'config.json').read_text());meta=json.loads((H/'environment.json').read_text())
pid=meta['pid'];cmdline=Path('/proc')/str(pid)/'cmdline'
if cmdline.exists():
 args=cmdline.read_bytes().split(b'\0');assert str(S/'runtime.py').encode()in args
 os.kill(pid,signal.SIGTERM)
manifest={}
for name in ('src','templates','static','locale'):
 for p in (R/name).rglob('*'):
  if not p.is_file()or '__pycache__'in p.parts or p.suffix=='.pyc':continue
  path=p.relative_to(R);dest=source/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());manifest[str(path)]=hashlib.sha256(dest.read_bytes()).hexdigest()
(H/'final-source-manifest.json').write_text(json.dumps(manifest,indent=2))
subprocess.run([str(R/'.venv/bin/python'),str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(source/'locale'),'--output',str(S/'locales-final'),'--compiler','native','--locales','ru','az','en'],check=True,capture_output=True)
settings_file=S/'settings.py';settings_file.write_text(settings_file.read_text().replace("QA_ROOT/'locales/locale'","QA_ROOT/'locales-final/locale'"))
(S/'qa_urls.py').write_bytes((H/'qa_urls.py').read_bytes());(S/'extend_fixtures.py').write_bytes((H/'extend_fixtures.py').read_bytes())
runtime=S/'runtime.py';runtime.write_text(runtime.read_text()+"\nelif sys.argv[1]=='extend':exec(compile((S/'extend_fixtures.py').read_text(),str(S/'extend_fixtures.py'),'exec'))\n")
subprocess.run([str(R/'.venv/bin/python'),str(runtime),'extend'],check=True,capture_output=True)
with(S/'final-server.log').open('w')as log:p=subprocess.Popen([str(R/'.venv/bin/python'),str(runtime),'serve'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
meta.update(pid=p.pid,source_files=len(manifest),url=f"http://127.0.0.1:{cfg['http_port']}",public_url=f"http://localhost:{cfg['http_port']}")
(H/'final-environment.json').write_text(json.dumps(meta,indent=2));print(json.dumps({'pid':p.pid,'source_files':len(manifest),'url':meta['url'],'public_url':meta['public_url']}))
