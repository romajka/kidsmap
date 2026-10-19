import json,hashlib,subprocess
from pathlib import Path
Q=Path(__file__).resolve().parent;R=Q.parents[1];O=R/'docs/qa/module09-full-2026-10-17-pc-r1';e=json.loads((R/'docs/qa/social-qa09-fix-2026-10-17-pc-r1/source-entry.json').read_text());git=json.loads((Q/'git-entry.json').read_text(encoding='utf-8-sig'))
assert git['head']=='852938d96764ae315b92859e3651e5ea62054a36' and git['branch']=='codex/module09-transfer-2026-10-16-r1' and not git['staged']
assert git['index_tree']=='881e0c48c7d557c46221beb3b2410a157982f861' and git['task33_ref']=='e4e05cc213b34e2d771ecb854901bfd016d1db51'
shared=e['shared_mo'];assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in shared.items())
(O/'safety-entry.json').write_text(json.dumps({'git':git,'shared_mo':shared,'active_run':'NONE','source1024':True,'external_transport':'Docker internal network; browser allowlist own loopback only','index_generation':'2026-10-16T18:56:53Z','metadata':'changed => direct source fallback'},indent=2))
print('Git/index/ref/sharedMO entry verified; no staged changes')
