import hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site19-pc-fix-r1';P=R/'docs/qa/site-qa19-recheck-2026-10-18-pc-r1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(O/'authorization.json')['application_implementation_authorized']
red=read(O/'evidence/red-backend.json');assert red['exit']==1 and red['failure_observations']==28 and len(red['failed_methods'])==7 and not red['errors']
entry=read(O/'source-entry.json');assert all(sha(R/p)==h for p,h in entry['sources'].items())
cand=read(P/'candidate-manifest.json');assert sha(P/'proposed.diff')==cand['diff_sha256']
for p,d in cand['files'].items():assert d['before_sha256']==(sha(R/p) if (R/p).exists() else None)
subprocess.run(['git','-C',str(R),'apply','--check',str(P/'proposed.diff')],check=True)
subprocess.run(['git','-C',str(R),'apply',str(P/'proposed.diff')],check=True)
for p,d in cand['files'].items():assert sha(R/p)==d['candidate_sha256']
changed=[p for p,h in entry['sources'].items() if sha(R/p)!=h];assert changed==['src/catalog/models/site.py']
source={p:sha(R/p) for p in entry['sources']};source['src/catalog/testcases/test_site_qa19_catalog_content.py']=sha(R/'src/catalog/testcases/test_site_qa19_catalog_content.py');assert len(source)==1032
(Q/'expected-source.json').write_text(json.dumps({'sources':source},indent=2));(O/'source-applied.json').write_text(json.dumps({'sources':source,'existing_changed':changed,'new':['src/catalog/testcases/test_site_qa19_catalog_content.py']},indent=2))
(Q/'stage.json').write_text(json.dumps({'locales':'locales-green','test_db':'test_m10s19_fix_r1_green'}))
cmd=['python3',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(R/'locale'),'--output',str(Q/'locales-green'),'--compiler','native'];r=subprocess.run(cmd,capture_output=True,text=True);(Q/'green-locales.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr[-500:]
(O/'applied.json').write_text(json.dumps({'approved_files':list(cand['files']),'exact_candidate_hashes':{p:sha(R/p) for p in cand['files']},'diff_sha256':sha(P/'proposed.diff'),'changed':changed,'new_sources':1,'total_sources':1032,'other_existing_sources_unchanged':1030,'fresh_green_db':'test_m10s19_fix_r1_green','locale_command':cmd,'locale_exit':r.returncode},indent=2));(O/'implemented.diff').write_bytes((P/'proposed.diff').read_bytes());print('Exact approved2file candidate applied;1030other sources unchanged; fresh GREEN DB/locales selected')
