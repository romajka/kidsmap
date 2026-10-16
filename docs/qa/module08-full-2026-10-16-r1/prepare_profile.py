import json,hashlib,shutil,socket,subprocess
from pathlib import Path
r=Path.cwd();h=r/'docs/qa/module08-full-2026-10-16-r1';s=r/'.tmp'/h.name;old=r/'.tmp/mod-qa08-fix-2026-10-16-r1'
assert (h/'entry.json').exists();cfg=json.loads((old/'config.json').read_text());c=json.loads(subprocess.check_output(['docker','inspect',cfg['container']],text=True))[0];assert c['Id']=='b4e125832fb38463089194b973c7bd25f61d3f4534d19bf6e079b6d1acb94766'and c['State']['Running'];assert c['NetworkSettings']['Ports']['5432/tcp']==[{'HostIp':'127.0.0.1','HostPort':'47955'}]
cfg['database']='module08_full_r1'
with socket.socket()as sock:sock.bind(('127.0.0.1',0));cfg['http_port']=sock.getsockname()[1]
(s/'config.json').write_text(json.dumps(cfg));shutil.copy2(old/'credentials.json',s/'credentials.json');(s/'credentials.json').chmod(0o600)
manifest=json.loads((h/'dependency-manifest.json').read_text());assert all(hashlib.sha256((old/'python-deps'/p).read_bytes()).hexdigest()==v for p,v in manifest.items());shutil.copytree(old/'python-deps',s/'python-deps');subprocess.run(['python3','-m','venv','--without-pip',str(s/'venv')],check=True);site=next((s/'venv/lib').glob('python*/site-packages'));(site/'qa-base.pth').write_text(str(r/'.venv/lib/python3.12/site-packages')+'\n');(h/'profile-reuse.json').write_text(json.dumps({'same_owned_pg_id':c['Id'],'loopback_port':47955,'new_database':cfg['database'],'http_port':cfg['http_port'],'existing_databases_modified':False},indent=2))
t=(r/'docs/qa/mod-qa08-recheck-2026-10-16-r1/create_owned_db.py').read_text().replace("=='mod08_plan_r1'","=='module08_full_r1'");(h/'create_owned_db.py').write_text(t)
print({'profile_ready':True,'http_port':cfg['http_port']})
