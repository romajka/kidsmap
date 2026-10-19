import json,hashlib,subprocess,socket,shutil
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social12-pc-fix-r1';P=R/'docs/qa/module09-close-2026-10-18-pc-r1';O=R/'docs/qa/social-qa12-fix-2026-10-18-pc-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not O.exists();O.mkdir();(O/'png').mkdir()
sources=json.loads((P/'source-final.json').read_text())['sources'];e=json.loads((P/'source-entry.json').read_text());m=json.loads((P/'candidate-manifest.json').read_text());assert len(sources)==1025 and all(sha(R/p)==h for p,h in sources.items())
g=json.loads((Q/'git-entry.json').read_text(encoding='utf-8-sig'));assert all(g[k]==e['git'][k] for k in ['head','branch','index_tree','task33_ref','staged']) and not g['staged']
assert not m['applied'] and len(m['files'])==3 and sha(P/'proposed-social12.diff')==m['diff_sha256'] and all(sha(P/'candidate'/p)==v['candidate_sha256'] and (sha(R/p)==v['before_sha256'] if v['before_sha256'] else not(R/p).exists()) for p,v in m['files'].items())
v=json.loads((P/'verification.json').read_text());assert v['backend_candidate_methods']==4 and v['backend_candidate_subtest_failures']==12 and v['expected_red_exit']==1 and v['backend_errors']==0
prior=e['prior_packages'];prior[P.name]={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()};assert len(prior)==20 and all(all(sha(O.parent/n/p)==h for p,h in fs.items()) for n,fs in prior.items())
pg=json.loads(subprocess.check_output(['docker','inspect','m09full-r1-pg']))[0];net=json.loads(subprocess.check_output(['docker','network','inspect','m09full-r1-net']))[0];safe={'pg_running':pg['State']['Running'],'owned_volume':any(x.get('Name')=='m09full-r1-pgdata' for x in pg['Mounts']),'no_pg_published_port':not any(pg['NetworkSettings']['Ports'].values()),'internal_network':net['Internal']};assert all(safe.values())
with socket.socket() as s:s.bind(('127.0.0.1',33440))
entry={'sources':sources,'shared_mo':e['shared_mo'],'prior_packages':prior,'git':g,'cbmignore':sha(R/'.cbmignore'),'guide_sha256':sha(R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md'),'containers':subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()}
(O/'source-entry.json').write_text(json.dumps(entry,indent=2));(O/'safety-entry.json').write_text(json.dumps(safe,indent=2));(O/'red-reference.json').write_text(json.dumps({'package':P.name,'current1025_matches_red_snapshot':True,'methods':4,'pass_methods':3,'failed_methods':1,'failed_subtests':12,'errors':0,'exit':1,'red_unchanged_not_repeated':True},indent=2))
for n in ['qa_settings.py','runtime.py','proxy.py','browser_driver.py','playwright.json']:
 t=(R/'.tmp/module09-pc-close-r1'/n).read_text().replace('module09-pc-close-r1','social12-pc-fix-r1').replace('test_m09close_r1','test_m09s12_fix_r1').replace('m09close-r1-app','m09s12-fix-r1-app').replace('m09-close-r1','s12-fix-r1').replace('33430','33440')
 (Q/n).write_text(t)
for p in m['files']:
 path=R/p;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((P/'candidate'/p).read_bytes())
expected={p:sha(R/p) for p in sources}
for p in m['files']:expected[p]=sha(R/p)
assert len(expected)==1027 and sum(sources[p]==expected[p] for p in sources)==1024 and all(sha(R/p)==v['candidate_sha256'] for p,v in m['files'].items())
(Q/'expected-source.json').write_text(json.dumps({'sources':expected},indent=2));(O/'applied.diff').write_bytes((P/'proposed-social12.diff').read_bytes());(O/'applied-manifest.json').write_text(json.dumps({'approved_by':'explicit user одобряю','files':m['files'],'diff_sha256':m['diff_sha256'],'source_files':1027,'other_original_unchanged':1024},ensure_ascii=False,indent=2))
print(json.dumps({'exact3_applied':True,'sources':1027,'other_original1024_unchanged':True,'prior_packages':20,'red_snapshot_verified':True,'safety':safe,'entry_containers':len(entry['containers'])}))
