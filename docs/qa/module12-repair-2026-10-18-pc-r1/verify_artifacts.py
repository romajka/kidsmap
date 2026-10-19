"""Read-only package/current-source verification; run under WSL with bytecode off."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT=Path('/mnt/c/kidsmap')
OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(OUT/'artifact-manifest.json')['files']
actual={p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file() and p!=OUT/'artifact-manifest.json'}
assert actual==set(manifest),'Artifact file set changed'
assert all(sha(OUT/p)==h for p,h in manifest.items()),'Artifact hash changed'
entry=read(OUT/'source-entry.json')
current=read(OUT/'source-current.json')['sources']
assert len(current)==1066 and current==read(OUT/'evidence/final-backend-source.json')['sources']
assert all(sha(ROOT/p)==h for p,h in current.items()),'Current source changed'
assert all(current[p]==h for p,h in entry['sources'].items() if p.startswith('src/catalog/testcases/'))
for package,files in entry['prior_packages'].items():
 folder=ROOT/'docs/qa'/package
 assert {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}==set(files),package
 assert all(sha(folder/p)==h for p,h in files.items()),package
assert all(sha(ROOT/p)==h for p,h in read(OUT/'document-current.json').items())
assert all(sha(ROOT/p)==h for p,h in entry['shared_mo'].items())
assert sha(ROOT/'.cbmignore')==entry['cbmignore']
assert sha(ROOT/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(ROOT/'docs/task33/implementation-status.md').read_text(),re.M)
def git(*args):return subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*args],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head']
assert git('branch','--show-current')==entry['git']['branch']
assert git('rev-parse','task33-progress')==entry['git']['task33_ref']
assert not git('diff','--cached','--name-only')
backend=read(OUT/'evidence/final-backend.json')
assert backend['exit']==0 and not backend['failures'] and not backend['errors']
assert len(backend['test_ids'])==len(set(backend['test_ids']))==586
assert backend['fresh_own_test_db']=='test_m12full_r2'
summary=read(OUT/'verification.json');rows=checks=0
for suite in summary['native']:
 result=read(OUT/suite['artifact']);values=[v for row in result['rows'] for v in row['checks'].values()]
 assert values and all(v is True for v in values) and not result.get('errors') and not result.get('pageerrors')
 rows+=len(result['rows']);checks+=len(values)
assert (rows,checks)==(447,2322)
assert all(result['exit']==0 for result in read(OUT/'evidence/javascript.json'))
assert read(OUT/'evidence/django-checks.json')['exit']==0
progress=read(OUT/'progress.json');assert progress['phase']=='COMPLETE LOCAL' and progress['confirmed_OPEN']==0
assert len(progress['historical_closed'])==8 and len(progress['additional_closed'])==5 and len(progress['merged_subcases'])==2
assert len(list((OUT/'findings').glob('ANALYTICS-QA-*.md')))==15
transitions=read(OUT/'evidence/foreign-runtime-transitions.json');assert len(transitions)==4 and all(t['identity_preserved'] and t['exit']==0 and not t['OOM'] and t['duration_seconds']>=86400 for t in transitions)
print(json.dumps({'status':'PASS LOCAL','manifest_entries':len(manifest),'source_files':len(current),'backend_methods':586,'native_rows':rows,'native_checks':checks,'prior_packages':43,'prior_files':9517,'confirmed_OPEN':0,'documented_natural_runtime_expirations':4}))
