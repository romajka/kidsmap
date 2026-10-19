import json,hashlib
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social11-pc-fix-r1';P=R/'docs/qa/social-qa11-recheck-2026-10-18-pc-r1';O=R/'docs/qa/social-qa11-fix-2026-10-18-pc-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((O/'source-entry.json').read_text());m=json.loads((P/'candidate-manifest.json').read_text());red=json.loads((Q/'red.json').read_text())
assert red['redFailures']==5 and (Q/'red.exit').read_text().strip()=='1'
assert all(sha(R/p)==h for p,h in e['sources'].items()) and sha(P/'proposed.diff')==m['diff_sha256']
assert all(sha(P/'candidate'/p)==v['candidate_sha256'] and sha(R/p)==v['before_sha256'] for p,v in m['files'].items())
for p in m['files']:(R/p).write_bytes((P/'candidate'/p).read_bytes())
expected={p:sha(R/p) for p in e['sources']};changed=[p for p,h in e['sources'].items() if expected[p]!=h];assert set(changed)==set(m['files'])
(Q/'expected-source.json').write_text(json.dumps({'sources':expected},indent=2));(O/'applied.diff').write_bytes((P/'proposed.diff').read_bytes());(O/'applied-manifest.json').write_text(json.dumps({'approved_by':'user дальше after exact three-file approval question','files':m['files'],'diff_sha256':m['diff_sha256'],'source_files':len(expected),'other_unchanged':len(expected)-len(changed)},ensure_ascii=False,indent=2));print(json.dumps({'applied':changed,'other_source_files_unchanged':1022,'source_files':1025}))
