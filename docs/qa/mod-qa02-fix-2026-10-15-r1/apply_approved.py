import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];P=R/'docs/qa/mod-qa02-recheck-2026-10-15-r1'
a=json.loads((H/'approval.json').read_text());assert hashlib.sha256((P/'IMPLEMENTATION_PLAN.md').read_bytes()).hexdigest()==a['plan_sha256'];assert hashlib.sha256((P/'proposed-MOD-QA-02.diff').read_bytes()).hexdigest()==a['diff_sha256']
red=json.loads((H/'regression-RED.status.json').read_text());text=(H/'regression-RED.output.txt').read_text();assert red['exit']==1 and 'FAILED (failures=12)'in text and '\nERROR:'not in text
for r in a['scope']:
 p=R/r['target'];v=P/r['proposal'];assert hashlib.sha256(v.read_bytes()).hexdigest()==r['proposal_sha256']
 if r['target'].endswith('test_mod_qa02_hub_media.py'):assert p.read_bytes()==v.read_bytes();continue
 assert not p.exists() if r['action']=='create'else hashlib.sha256(p.read_bytes()).hexdigest()==r['before_sha256']
for r in a['scope']:
 if r['target'].endswith('test_mod_qa02_hub_media.py'):continue
 p=R/r['target'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((P/r['proposal']).read_bytes())
(H/'applied-manifest.json').write_text(json.dumps([{**r,'actual_sha256':hashlib.sha256((R/r['target']).read_bytes()).hexdigest()}for r in a['scope']],indent=2))
paths=[]
for root in ('src','static','templates','config'):
 for p in (R/root).rglob('*'):
  if p.is_file()and p.suffix in{'.py','.html','.css','.js'}:paths.append(str(p.relative_to(R)))
(H/'source-paths.json').write_text(json.dumps(sorted(set(paths)),indent=2));print(json.dumps({'applied_exact_files':len(a['scope']),'source_paths':len(set(paths))}))
