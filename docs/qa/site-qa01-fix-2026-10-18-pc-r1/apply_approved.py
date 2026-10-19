import hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site01-pc-fix-r1';P=R/'docs/qa/site-qa01-recheck-2026-10-18-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((P/'candidate-manifest.json').read_text())
assert json.loads((O/'evidence/red-backend.json').read_text())['failed_observations']==31
assert json.loads((O/'evidence/red-backend.json').read_text())['errors']==0
for p,d in m['files'].items():
 assert (sha(R/p) if (R/p).exists() else None)==d['before_sha256']
 if (R/p).exists():
  target=O/'entry-source'/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((R/p).read_bytes())
subprocess.run(['git','-C',str(R),'apply','--check',str(P/'proposed.diff')],check=True)
subprocess.run(['git','-C',str(R),'apply',str(P/'proposed.diff')],check=True)
after={p:sha(R/p) for p in m['files']}
assert all(after[p]==d['candidate_sha256'] for p,d in m['files'].items())
entry=json.loads((O/'source-entry.json').read_text())
assert all(sha(R/p)==h for p,h in entry['sources'].items() if p not in m['files'])
sources={p:sha(R/p) for p in set(entry['sources'])|set(m['files'])}
(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2))
(O/'apply.json').write_text(json.dumps({'git_apply_exit':0,'files':after,'exact_candidate_match':True,'source_total':len(sources),'unrelated_source_preserved':True},indent=2))
print(json.dumps({'exact4file_patch_applied':True,'source_total':len(sources),'unrelated_source_preserved':True}))
