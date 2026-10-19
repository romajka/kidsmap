import hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site08-pc-fix-r1';P=O.parent/'site-qa08-recheck-2026-10-18-pc-r1';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(O/'authorization.json')['application_implementation_authorized'];entry=read(O/'source-entry.json');assert len(entry['sources'])==1032 and all(sha(R/p)==h for p,h in entry['sources'].items())
red=read(O/'evidence/browser-acceptance-red.json');assert len(red['rows'])==162 and not red['pageerrors'] and not red['local_errors'] and red['no_fixture_write']
failed=[k for r in red['rows'] for k,v in r['checks'].items() if not v];assert len(failed)==314 and set(failed)<={'no_document_overflow','fields_in_viewport','cards_within_main','cards_not_covered_by_actions','save_accessible'}
for name,rows in [('browser-readonly-red',18),('browser-sentinels-red',12)]:
 d=read(O/'evidence'/f'{name}.json');assert len(d['rows'])==rows and all(all(r['checks'].values()) for r in d['rows']) and d['no_fixture_write'] and not d['pageerrors'] and not d['local_errors']
cand=read(P/'candidate-manifest.json');assert len(cand['files'])==2 and sha(P/'proposed.diff')==cand['diff_sha256']
for p,d in cand['files'].items():assert (not (R/p).exists()) if d['new'] else sha(R/p)==d['before_sha256']
assert sha(R/'.git/index')==entry['git']['index_sha256'];subprocess.run(['git','-C',str(R),'apply','--check',str(P/'proposed.diff')],check=True)
setup=read(O/'evidence/setup.json');assert subprocess.check_output(['docker','inspect','m10s08-fix-r1-app','--format','{{.Id}}'],text=True).strip()==setup['container_id']
stop="import os,signal,time;from pathlib import Path\nq=Path('/mnt/c/kidsmap/.tmp/site08-pc-fix-r1');pid=int((q/'server.pid').read_text());proc=Path('/proc/'+str(pid)+'/cmdline');cmd=proc.read_bytes().split(bytes([0]));assert str(q/'runtime.py').encode() in cmd and b'serve' in cmd\nos.kill(pid,signal.SIGTERM)\nfor i in range(50):\n if not proc.exists() or str(q/'runtime.py').encode() not in proc.read_bytes():break\n time.sleep(.1)\nelse:raise AssertionError('Own server did not stop')\nprint('Verified own server stopped')"
r=subprocess.run(['docker','exec','m10s08-fix-r1-app','python','-c',stop],capture_output=True,text=True);assert r.returncode==0,r.stderr
subprocess.run(['git','-C',str(R),'apply',str(P/'proposed.diff')],check=True)
for p,d in cand['files'].items():assert sha(R/p)==d['candidate_sha256']
changed=[p for p,h in entry['sources'].items() if sha(R/p)!=h];new=[p for p,d in cand['files'].items() if d['new']];assert changed==[p for p,d in cand['files'].items() if not d['new']] and len(new)==1
sources={p:sha(R/p) for p in entry['sources']};sources.update({p:sha(R/p) for p in new});assert len(sources)==1033
(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2));(O/'source-applied.json').write_text(json.dumps({'sources':sources,'changed':changed,'new':new},indent=2));(O/'implemented.diff').write_bytes((P/'proposed.diff').read_bytes())
(O/'applied.json').write_text(json.dumps({'approved_files':list(cand['files']),'exact_candidate_hashes':{p:sha(R/p) for p in cand['files']},'source_count':1033,'other_existing_sources_unchanged':1031,'old_own_server_stopped_verified':True,'fresh_test_db':'test_m10s08_fix_r1','application_refinements':0},indent=2));print('Exact2file candidate applied;1031other existing sources unchanged; only own server stopped.')
