import hashlib,json,socket,subprocess,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
old=json.loads((H/'server.json').read_text());p=Path('/proc')/str(old['pid']);assert not p.exists(),'Old PID must be inspected separately, never stopped implicitly'
expected=json.loads((H/'runtime-source-baseline.json').read_text());assert all(hashlib.sha256((R/f).read_bytes()).hexdigest()==v for f,v in expected.items())
with socket.socket()as sock:sock.bind(('127.0.0.1',int(old['url'].rsplit(':',1)[1])))
container=subprocess.check_output(['docker','ps','--filter','name=^/'+old['container']+'$','--format','{{.ID}}'],text=True).strip();assert(H/'docker-start.txt').read_text().strip().startswith(container)and container
(H/'server-before-interruption.json').write_bytes((H/'server.json').read_bytes())
with(S/'server-resumed.log').open('wb')as log:new=subprocess.Popen(old['argv'],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
old['pid']=new.pid;(H/'server.json').write_text(json.dumps(old,indent=2))
for _ in range(100):
 try:
  source=json.load(urllib.request.urlopen(old['url']+'/qa/source/',timeout=1))
  if source['pid']==new.pid:break
 except Exception:pass
 time.sleep(.1)
else:raise AssertionError('Own HTTP not ready')
assert source['startup_matches_disk'];(H/'runtime-source-resumed.json').write_text(json.dumps(source,indent=2))
note={'event':'Explicit turn interruption; old own server PID and owned browser session no longer available; five captured older QA process identities also unavailable. No signal/kill/restart was sent to foreign processes. Cause of disappearance UNKNOWN. Existing own PostgreSQL container identity preserved; no migrate/reseed/reinvite repeated. Only own HTTP and own new browser will be started.','old_foreign_process_preservation':'NOT VERIFIED','files_and_containers':'final gate will compare separately','resumed_pid':new.pid}
(H/'interruption.json').write_text(json.dumps(note,indent=2))
with(H/'commands.jsonl').open('a')as f:f.write(json.dumps({'name':'resume-owned-http','argv':old['argv'],'exit':0,'new_pid':new.pid,'signals_to_foreign_processes':0,'no_migrate_reseed':True})+'\n')
print({'pid':new.pid,'source_match':True,'same_own_pg':True})
