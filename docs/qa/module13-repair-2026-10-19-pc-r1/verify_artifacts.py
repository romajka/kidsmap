"""Read-only Module13 evidence/source/preservation verifier. No Django or DB writes."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
O = Path(__file__).resolve().parent
R = O.parents[2]
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = read(O/'artifact-manifest.json')['files']
assert {p.relative_to(O).as_posix() for p in O.rglob('*') if p.is_file()} == set(manifest)|{'artifact-manifest.json'}
assert all(sha(O/p) == h for p,h in manifest.items())
source = read(O/'source-current.json')
assert all(sha(R/p) == h for p,h in source['sources'].items())
entry = read(O/'source-entry.json')
for name, files in entry['prior_packages'].items():
    folder = O.parent/name
    assert {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()} == set(files)
    assert all(sha(folder/p) == h for p,h in files.items())
assert all(sha(R/p) == h for p,h in read(O/'document-current.json').items())
for p, record in read(O/'evidence/document-appends.json').items():
    assert hashlib.sha256((R/p).read_bytes()[:record['original_prefix_length']]).hexdigest() == record['original_prefix_sha256']
    assert sha(R/p) == record['final_sha256']
assert sha(R/'.git/index') == entry['git']['index_sha256']
git_exe = '/mnt/c/Program Files/Git/cmd/git.exe' if str(R).startswith('/mnt/c/') else 'git'
git_root = 'C:/kidsmap' if str(R).startswith('/mnt/c/') else str(R)
git = lambda *args: subprocess.check_output([git_exe,'-C',git_root,*args], text=True).strip()
assert git('rev-parse','HEAD') == entry['git']['head']
assert git('branch','--show-current') == entry['git']['branch']
assert git('rev-parse','task33-progress') == entry['git']['task33_ref']
assert not git('diff','--cached','--name-only')
assert sha(R/'.cbmignore') == entry['cbmignore']
assert all(sha(R/p) == h for p,h in entry['shared_mo'].items())
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
v = read(O/'verification.json')
backend = read(O/'evidence/qa04-r5-backend.json')
discovery = read(O/'evidence/discovery-current.json')
assert backend['exit'] == 0 and backend['unique_methods'] == 2626 and not backend['failures'] and not backend['errors'] and 'OK' in backend['summary']
assert set(backend['ids']) == set(discovery['exhaustive']['ids']) == set(discovery['no_label']['ids'])
assert not discovery['no_label']['duplicates']
assert read(O/'evidence/node-final.json')['TAP_counts'] == {'tests':'129','pass':'129','fail':'0','skipped':'0'}
assert read(O/'evidence/python-final.json')['exit'] == read(O/'evidence/python-windows-locales-final.json')['exit'] == 0
assert v['confirmed_OPEN'] == 0 and v['original_assertions_preserved'] == 225
for suite in v['native']:
    d = read(O/suite['artifact'])
    assert not any(d.get(k) for k in ['error','errors','pageerrors','consoleRows'])
    checks = [x for row in d['rows'] for x in row.get('checks',{}).values()]
    assert len(d['rows']) == suite['rows'] and len(checks) == suite['checks'] and all(x is True for x in checks)
assert sum(x['rows'] for x in v['native']) == v['native_rows'] == 394
assert sum(x['checks'] for x in v['native']) == v['native_checks'] == 1501
assert read(O/'evidence/ci-structure.json')['deploy_job_byte_identical']
assert read(O/'evidence/preservation.json')['prior_hashes_and_sets_unchanged']
print(json.dumps({'status':'PASS LOCAL Module13 sealed evidence','manifest_entries':len(manifest),
    'source_files':len(source['sources']),'backend_unique_methods':2626,'backend_failures':0,'backend_errors':0,
    'JavaScript_TAP_pass':129,'native_rows':394,'native_checks':1501,'prior_packages':len(entry['prior_packages']),
    'prior_files':sum(map(len,entry['prior_packages'].values())),'confirmed_OPEN':0,
    'original_assertions_preserved':225,'documented_natural_runtime_expirations':len(read(O/'evidence/foreign-runtime-transitions.json'))},indent=2))
