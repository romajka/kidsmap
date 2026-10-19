import hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site15-pc-fix-r1';P=R/'docs/qa/site-qa15-recheck-2026-10-18-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
red=json.loads((O/'evidence/red-backend.json').read_text());assert red['exit']==1 and red['errors']==0 and red['failed_method_count']==16
m=json.loads((P/'candidate-manifest.json').read_text());entry=json.loads((O/'source-entry.json').read_text())
assert all(sha(R/p)==h for p,h in entry['sources'].items())
for p,d in m['files'].items():
 assert (sha(R/p) if (R/p).exists() else None)==d['before_sha256']
 if (R/p).exists():
  target=O/'entry-source'/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((R/p).read_bytes())
subprocess.run(['git','-C',str(R),'apply','--check',str(P/'proposed.diff')],check=True)
subprocess.run(['git','-C',str(R),'apply',str(P/'proposed.diff')],check=True)
assert all(sha(R/p)==d['candidate_sha256'] for p,d in m['files'].items())
sources={p:sha(R/p) for p in set(entry['sources'])|{p for p in m['files'] if p.endswith('.py')}}
assert len(sources)==1029
assert all(sha(R/p)==h for p,h in entry['sources'].items() if p not in m['files'])
(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2))
cmd=['python3',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(R/'locale'),'--output',str(Q/'locales-green'),'--compiler','native']
r=subprocess.run(cmd,capture_output=True,text=True);(O/'evidence/green-locales.json').write_text(json.dumps({'command':cmd,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2));assert r.returncode==0
(Q/'stage.json').write_text(json.dumps({'name':'green','locales':'locales-green'}))
(O/'apply.json').write_text(json.dumps({'exact6candidate_files_applied':True,'files':{p:sha(R/p) for p in m['files']},'source_total':1029,'unrelated_sources_preserved':True,'fresh_green_locales':True},indent=2))
print(json.dumps({'exact6file_patch':True,'source_total':1029,'green3MO_fresh':True,'unrelated_sources_preserved':True}))
