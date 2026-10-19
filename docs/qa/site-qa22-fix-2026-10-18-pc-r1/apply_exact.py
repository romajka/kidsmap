import hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;P=O.parent/'site-qa22-recheck-2026-10-18-pc-r1';Q=R/'.tmp/site22-pc-fix-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
entry=read(O/'source-entry.json');candidate=read(O/'approved-candidate-manifest.json');setup=read(O/'evidence/setup.json');red=read(O/'evidence/red-backend.json');assert red['exit']==1 and red['failure_observations']==20 and not red['errors']
assert len(entry['sources'])==1033 and all(sha(R/p)==h for p,h in entry['sources'].items())
focused=read(O/'evidence/browser-focused-red.json');assert sum(v is False for r in focused['rows'] for v in r['checks'].values())==6 and not focused['pageerrors'] and not focused['local_errors']
sentinel=read(O/'evidence/browser-sentinels-red.json');assert sentinel['no_fixture_write'] and all(all(r['checks'].values()) for r in sentinel['rows'])
assert sha(O/'implemented.diff')==sha(P/'proposed.diff')==candidate['diff_sha256'];check=subprocess.run(['git','-C',str(R),'apply','--check',str(O/'implemented.diff')],capture_output=True,text=True);assert check.returncode==0,check.stderr
for p,d in candidate['files'].items():
 assert sha(P/'candidate'/p)==d['candidate_sha256']
 if d['before_sha256']:assert sha(R/p)==d['before_sha256']
 else:assert not (R/p).exists()
assert subprocess.check_output(['docker','inspect',setup['app'],'--format','{{.Id}}'],text=True).strip()==setup['container_id']
pid=int((Q/'server.pid').read_text());stopcode='''import os,sys,time
pid=int(sys.argv[1]);expected=sys.argv[2];cmd=open('/proc/'+str(pid)+'/cmdline','rb').read().split(b'\\0');assert expected.encode() in cmd and b'serve' in cmd;os.kill(pid,15)
for i in range(100):
 if not os.path.exists('/proc/'+str(pid)):print('owned-server-stopped');break
 time.sleep(.1)
else:raise AssertionError('Own server did not stop')
'''
stop=subprocess.run(['docker','exec',setup['app'],'python','-c',stopcode,str(pid),str(Q/'runtime.py')],capture_output=True,text=True);assert stop.returncode==0,stop.stderr
for p,d in candidate['files'].items():
 if d['before_sha256']:
  backup=O/'entry-source'/p;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes((R/p).read_bytes())
 target=R/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((P/'candidate'/p).read_bytes());assert sha(target)==d['candidate_sha256']
sources={p:sha(R/p) for p in entry['sources']}
for p in candidate['files']:sources[p]=sha(R/p)
assert len(sources)==1034 and len([p for p,h in entry['sources'].items() if sources[p]==h])==1031
(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2));(O/'source-applied.json').write_text(json.dumps({'sources':sources},indent=2));(O/'applied.json').write_text(json.dumps({'approved_files':list(candidate['files']),'exact_candidate_hashes_verified':True,'source_count':1034,'changed_existing':2,'new_tests':1,'other_existing_sources_unchanged':1031,'application_refinements':0,'apply_check_exit':check.returncode,'old_own_server_stopped_verified':True,'old_own_server_pid':pid,'container_id_verified':setup['container_id'],'method':'Exact approved candidate bytes after apply--check; old CRLF and existing whitespace retained'},indent=2));print('Exact3file SITE22 patch applied;1031other existing source files unchanged.')
