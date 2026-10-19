"""Read-only package/source verification; no Django imports or application writes."""
import hashlib,json,subprocess,re
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());manifest=read(O/'artifact-manifest.json')
assert {p.relative_to(O).as_posix() for p in O.rglob('*') if p.is_file()}==set(manifest)|{'artifact-manifest.json'}
assert all(sha(O/p)==h for p,h in manifest.items())
final=read(O/'source-final.json');entry=read(O/'source-entry.json');assert all(sha(R/p)==h for p,h in final['sources'].items());assert all(sha(R/p)==h for p,h in read(O/'document-current.json').items());assert all(sha(R/p)==h for p,h in entry['shared_mo'].items());assert sha(R/'.cbmignore')==entry['cbmignore'];assert sha(R/'.git/index')==entry['git']['index_sha256'];assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
assert all(final['sources'][p]==h for p,h in entry['sources'].items() if p.startswith('src/catalog/testcases/'))
v=read(O/'verification.json');p=read(O/'progress.json');assert p['remaining_OPEN']==0 and len(p['closed'])==15 and p['full_module_acceptance']=='PASS LOCAL' and v['final_backend_methods']==238 and v['final_public_FAIL']==0
print(json.dumps({'artifact_files':len(manifest),'artifact_hashes_and_file_set':'PASS','current_source_files':len(final['sources']),'source_and_document_hashes':'PASS','all_preexisting_test_sources_unchanged':True,'shared_MO_index_cbmignore_active_run':'PASS','closed_remaining_findings':15,'final_backend_methods':238,'final_public_checks':v['final_public_checks'],'status':'PASS LOCAL'},indent=2))
