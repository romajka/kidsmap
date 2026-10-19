import hashlib,json,os,subprocess,time
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;F=O.parent/'site-qa08-fix-2026-10-18-pc-r1';Q=R/'.tmp/site08-pc-followup-r1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
entry=read(O/'source-entry.json');cand=read(O/'candidate-manifest.json');setup=read(O/'evidence/setup.json');assert all(sha(R/p)==h for p,h in entry['sources'].items())
red=read(O/'evidence/browser-message-red.json');assert red['rows'][2]['geometry']['document']==366 and red['rows'][2]['geometry']['alert_display']=='flex' and red['rows'][2]['checks']=={'no_document_overflow':False}
sentinel=read(O/'evidence/browser-sentinels-red.json');assert sentinel['no_fixture_write'] and all(all(r['checks'].values()) for r in sentinel['rows'])
assert sha(O/'implemented.diff')==cand['diff_sha256']==sha(F/'followup/proposed.diff')
check=subprocess.run(['git','-C',str(R),'apply','--check',str(O/'implemented.diff')],capture_output=True,text=True);assert check.returncode==0,check.stderr
assert subprocess.check_output(['docker','inspect',setup['app'],'--format','{{.Id}}'],text=True).strip()==setup['container_id']
pid=int((Q/'server.pid').read_text());expected=str(Q/'runtime.py')
stopcode='''import os,sys,time
pid=int(sys.argv[1]);expected=sys.argv[2];cmd=open('/proc/'+str(pid)+'/cmdline','rb').read().split(b'\\0');assert expected.encode() in cmd and b'serve' in cmd,cmd;os.kill(pid,15)
for i in range(100):
 if not os.path.exists('/proc/'+str(pid)):print('owned-server-stopped');break
 time.sleep(.1)
else:raise AssertionError('Own server did not stop')
'''
stop=subprocess.run(['docker','exec',setup['app'],'python','-c',stopcode,str(pid),expected],capture_output=True,text=True);assert stop.returncode==0,stop.stderr
changed=[]
for p,d in cand['files'].items():
 assert sha(R/p)==d['before_sha256'] and sha(F/'followup/candidate'/p)==d['candidate_sha256'];(R/p).write_bytes((F/'followup/candidate'/p).read_bytes());assert sha(R/p)==d['candidate_sha256'];changed.append(p)
sources={p:sha(R/p) for p in entry['sources']};assert [p for p,h in entry['sources'].items() if h!=sources[p]]==changed
(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2));(O/'source-applied.json').write_text(json.dumps({'sources':sources},indent=2))
(O/'applied.json').write_text(json.dumps({'approved_files':changed,'application_refinements':0,'source_count':1033,'other_existing_sources_unchanged':1032,'old_own_server_stopped_verified':True,'old_own_server_pid':pid,'container_id_verified':setup['container_id'],'apply_check_exit':check.returncode,'method':'Exact approved candidate bytes after git apply --check; CRLF preserved','candidate_hashes_verified':True},indent=2))
print('Exact approved one-CSS candidate applied;1032other source hashes unchanged.')
