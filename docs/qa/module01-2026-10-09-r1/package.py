"""Read-only final evidence capture; credentials never enter artifacts."""
import csv, hashlib, json, subprocess, sys, urllib.request
from pathlib import Path
here=Path(__file__).resolve().parent
root=here.parents[2]
def command(args):
    p=subprocess.run(args,cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace')
    return {'argv':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def result(name):
    text=(here/name).read_text(encoding='utf-8')
    return json.JSONDecoder().raw_decode(text.strip())[0]
cells=result('matrix.result.txt')['rows']
cells += [r for r in result('deep-matrix.result.txt')['rows'] if r['id'].startswith('owner/')]
cells += result('deep-admin-final.result.txt')['rows']
assert len(cells)==234 and len({r['id'] for r in cells})==234
(here/'matrix.json').write_text(json.dumps(cells,ensure_ascii=False,indent=2),encoding='utf-8')
with (here/'matrix.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['id','status','lang','width','screenshot']);w.writeheader()
    w.writerows({k:r.get(k,'') for k in w.fieldnames} for r in cells)
observations=command([sys.executable,str(here/'observe.py')])
assert observations['exit_code']==0
(here/'observations.txt').write_text(observations['stdout'],encoding='utf-8')
snapshot=json.loads((here/'snapshot.json').read_text(encoding='utf-8'))
changed=[name for name,digest in snapshot['source_files'].items() if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest]
version=json.load(urllib.request.urlopen('http://localhost:8811/qa/version/'))
git={k:command(args) for k,args in {
    'head':['git','rev-parse','HEAD'], 'branch':['git','branch','--show-current'],
    'status':['git','status','--short'], 'diff_check':['git','diff','--check'],
    'tracked_diff':['git','diff','--name-only'],
    'scratch_ignored':['git','check-ignore','.tmp/module01-20261009-r1/credential'],
    'containers':['wsl','-d','Ubuntu-24.04','--','docker','ps','--format','{{.Names}}:{{.Ports}}']}.items()}
credential=(root/'.tmp/module01-20261009-r1/credential').read_text()
leaks=[]
for p in here.rglob('*'):
    if p.is_file() and p.suffix in {'.py','.js','.json','.jsonl','.txt','.md','.csv'}:
        if credential.encode() in p.read_bytes() or (b'synthetic-'+b'local-only') in p.read_bytes():leaks.append(p.relative_to(here).as_posix())
manifest=[]
for p in sorted((here/'screenshots').glob('*.png')):
    from PIL import Image
    with Image.open(p) as im: width,height=im.size
    manifest.append({'path':p.relative_to(here).as_posix(),'width':width,'height':height,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(here/'screenshots-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
summary={'source_files_verified':len(snapshot['source_files']),'source_files_changed':changed,
    'runtime':version,'git':git,'matrix_cells':len(cells),
    'matrix_status':{s:sum(r['status']==s for r in cells) for s in ['PASS','FAIL','NOT RUN']},
    'screenshots':len(manifest),'credential_scan_leaks':leaks,
    'active_run_existing':'NONE (unchanged)','qa_run_status':'AUDIT COMPLETE / FAIL; remaining NOT RUN detailed in REPORT.md',
    'executor':'/root sequential; no independent sub-agent execution',
    'backend':json.loads((here/'backend-result.json').read_text(encoding='utf-8'))}
(here/'verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
assert not changed and not leaks
assert git['head']['stdout'].strip()==snapshot['head']
assert git['diff_check']['exit_code']==0
print(json.dumps({k:summary[k] for k in ['source_files_verified','source_files_changed','matrix_cells','matrix_status','screenshots','credential_scan_leaks']},ensure_ascii=False))
