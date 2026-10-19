from pathlib import Path
import hashlib,json
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
p=R/'src/catalog/testcases/test_module13_event_projection.py';t=p.read_text();assert "'offline'" in t;p.write_text(t.replace("'offline'","'physical'"))
d=json.loads((Q/'expected-source.json').read_text());d['sources'][p.relative_to(R).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest();(Q/'expected-source.json').write_text(json.dumps(d,indent=2))
(O/'evidence/fixture-correction.md').write_text('Own new regression r1 used invalid format offline instead of actual physical enum; one fixture ERROR. Corrected the new fixture before accepted RED. Retain r1 failure evidence; no existing assertion or application source changed.\n')
