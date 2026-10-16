"""Start/reuse only this QA profile; never stop another process."""
import json, subprocess, time, urllib.request
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SCRATCH=ROOT/'.tmp'/HERE.name
config=json.loads((SCRATCH/'config.json').read_text())
server_file=HERE/'server.json'
server=json.loads(server_file.read_text()) if server_file.exists() else {}
proc_path=Path('/proc')/str(server.get('pid',0))
if not proc_path.exists():
    log=(SCRATCH/'server.log').open('a')
    proc=subprocess.Popen([str(ROOT/'.venv/bin/python'),str(HERE/'runtime.py'),'serve'],
                          stdout=log,stderr=log,start_new_session=True)
    server={'pid':proc.pid,'url':f"http://127.0.0.1:{config['http_port']}",
            'database':config['database'],'script':str(HERE/'runtime.py')}
    server_file.write_text(json.dumps(server))
else:
    assert str(HERE/'runtime.py').encode() in (proc_path/'cmdline').read_bytes()
for attempt in range(30):
    try:
        data=json.load(urllib.request.urlopen(server['url']+'/qa/start-version/',timeout=3))
        break
    except Exception:
        time.sleep(.5)
else:
    raise RuntimeError('Own QA runtime unavailable')
assert data['testing'] and data['pid']==server['pid']
assert data['entry_matches_startup'] and data['startup_matches_disk']
(HERE/'runtime-version-final.json').write_text(json.dumps(data,indent=2))
print(json.dumps({'url':server['url'],'pid':server['pid'],'source_match':True}))
