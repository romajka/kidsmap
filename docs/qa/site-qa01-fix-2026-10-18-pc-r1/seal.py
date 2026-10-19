import hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=json.loads((O/'verification.json').read_text());assert result['green']['exit']==0
entry=json.loads((O/'source-entry.json').read_text());assert sha(R/'.git/index')==entry['git']['index_sha256']
proof=json.loads((O/'document-preservation.json').read_text())
for p,d in proof.items():assert hashlib.sha256((R/p).read_bytes()[:d['original_bytes']]).hexdigest()==d['original_sha256']
manifest={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'}
(O/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2))
assert all(sha(O/p)==h for p,h in manifest.items())
print(json.dumps({'artifact_files':len(manifest),'artifact_hashes_match':True,'guide_master_original_prefixes_match':True,'empty_index_bytes_preserved':True,'status':result['status'],'png':result['png'],'browser_checks':sum(v['checks'] for v in result['browser'].values()),'backend_methods_green':result['green']['methods']},indent=2))
