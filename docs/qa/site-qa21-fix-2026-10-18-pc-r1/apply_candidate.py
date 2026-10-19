import hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site21-pc-fix-r1';P=R/'docs/qa/site-qa21-recheck-2026-10-18-pc-r1';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(O/'authorization.json')['application_implementation_authorized']
entry=read(O/'source-entry.json');assert len(entry['sources'])==1032 and all(sha(R/p)==h for p,h in entry['sources'].items())
red=read(O/'evidence/browser-acceptance-stable-red.json');assert len(red['rows'])==36 and not red['pageerrors'] and not red['local_errors']
failed=[k for r in red['rows'] for k,v in r['checks'].items() if not v];assert failed and set(failed)<={'fills_available_column','visible_cards_within_main','cards_not_covered_by_actions','visible_fields_within_main'}
desktop=[r for r in red['rows'] if r['width'] in [1280,1440]];assert len(desktop)==12 and all(not r['checks']['cards_not_covered_by_actions'] for r in desktop)
sentinel=read(O/'evidence/browser-sentinels-red.json');assert len(sentinel['rows'])==18 and all(all(r['checks'].values()) for r in sentinel['rows'])
cand=read(P/'candidate-manifest.json');assert len(cand['files'])==1 and sha(P/'proposed.diff')==cand['diff_sha256']
for p,d in cand['files'].items():assert sha(R/p)==d['before_sha256']
assert sha(R/'.git/index')==entry['git']['index_sha256']
subprocess.run(['git','-C',str(R),'apply','--check',str(P/'proposed.diff')],check=True)
setup=read(O/'evidence/setup.json');assert subprocess.check_output(['docker','inspect','m10s21-fix-r1-app','--format','{{.Id}}'],text=True).strip()==setup['container_id']
stop="import os,signal,time;from pathlib import Path\nq=Path('/mnt/c/kidsmap/.tmp/site21-pc-fix-r1');pid=int((q/'server.pid').read_text());proc=Path('/proc/'+str(pid)+'/cmdline');cmd=proc.read_bytes().split(bytes([0]));assert str(q/'runtime.py').encode() in cmd and b'serve' in cmd\nos.kill(pid,signal.SIGTERM)\nfor i in range(50):\n if not proc.exists() or str(q/'runtime.py').encode() not in proc.read_bytes():break\n time.sleep(.1)\nelse:raise AssertionError('Own server did not stop')\nprint('Verified own server stopped')"
stopped=subprocess.run(['docker','exec','m10s21-fix-r1-app','python','-c',stop],capture_output=True,text=True);assert stopped.returncode==0,stopped.stderr
subprocess.run(['git','-C',str(R),'apply',str(P/'proposed.diff')],check=True)
for p,d in cand['files'].items():assert sha(R/p)==d['candidate_sha256']
changed=[p for p,h in entry['sources'].items() if sha(R/p)!=h];assert changed==list(cand['files'])
sources={p:sha(R/p) for p in entry['sources']};(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2));(O/'source-applied.json').write_text(json.dumps({'sources':sources,'changed':changed},indent=2));(O/'implemented.diff').write_bytes((P/'proposed.diff').read_bytes())
(O/'applied.json').write_text(json.dumps({'approved_files':changed,'exact_candidate_hashes':{p:sha(R/p) for p in changed},'source_count':1032,'other_sources_unchanged':1031,'old_own_server_stopped_verified':True,'fresh_test_db':'test_m10s21_fix_r1','application_refinements':0},indent=2));print('Exact approved one-line template change applied;1031other sources unchanged; only verified own server stopped')
