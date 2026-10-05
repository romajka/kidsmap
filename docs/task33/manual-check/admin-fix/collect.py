"""Read-back verification; only owned QA evidence is copied. No application writes."""
import hashlib, json, shutil, subprocess, urllib.request
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
manifest = read(HERE.parent / 'source-manifest.json')
for item in manifest['source_files']:
    for root in (REPO, Path(manifest['runtime_root'])):
        assert sha(root / item['path']) == item['sha256'], item['path']
baseline = read(HERE / 'before/docs/task33/manual-check/source-manifest.json')
for item in baseline['source_files']:
    assert sha(Path(baseline['runtime_root']) / item['path']) == item['sha256']
old_completion = read(REPO / 'docs/task33/completion/final-verification.json')
for item in old_completion['source_files']:
    assert sha(Path('/root/km-completion-browser') / item['path']) == item['sha256']
historical = {}
for area, name in [('completion','evidence-manifest.json'),('final-audit','artifact-manifest.json')]:
    root = REPO / 'docs/task33' / area
    items = read(root / name)['files']
    for item in items: assert sha(root / item['path']) == item['sha256'], item['path']
    historical[area] = len(items)
audit_entry = read(REPO/'docs/task33/completion/entry.json')['immutable_audit']
for item in audit_entry:
    assert sha(REPO/item['path']) == item['sha256'], item['path']
historical['final-audit_entry_complete'] = len(audit_entry)
entry = read(HERE / 'entry.json')
for item in entry: assert sha(HERE / 'before' / item['path']) == item['sha256']
preserved = [{'path':str(p.relative_to(HERE/'before')), 'sha256':sha(p)} for p in sorted((HERE/'before').rglob('*')) if p.is_file()]
(HERE/'preserved-files.json').write_text(json.dumps(preserved,indent=2)+'\n')
backend = Path('/tmp/task33-adminrepair-final-20261004-1820')
target = HERE / 'backend'
target.mkdir(exist_ok=True)
for name in ['run.json','suite-results.json','checks.json','migrations.json','isolation.json','safety.log']:
    shutil.copyfile(backend/name, target/name)
suite = read(target/'suite-results.json'); run = read(target/'run.json')
assert suite['status'] == run['status'] == run['cleanup'] == 'PASS'
assert suite['tests_run'] == 270 and not suite['failures'] and not suite['errors'] and not suite['skipped']
backend_files = {i['path']:i['sha256'] for i in read(HERE/'backend-source-snapshot.json')['source_files']}
backend_delta = [i['path'] for i in manifest['source_files'] if backend_files[i['path']] != i['sha256']]
assert backend_delta == ['static/admin/css/pages/kidsmap_changelist.css'], backend_delta
def browser_result(log):
    lines = log.read_text().splitlines()
    return json.loads(next(s for s in lines if s.startswith('{"status"')))
matrix = browser_result(HERE/'browser-matrix-final.log')
assert matrix['status'] == 'PASS' and matrix['count'] == 366
(HERE/'browser-matrix.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
mobile = read(HERE/'browser-mobile.json')
assert mobile['status'] == 'PASS' and len(mobile['rows']) == 27
screens = ['admin-organizations-before.png','admin-place-menu-mobile.png'] + ['admin-repaired-'+m+'-'+str(w)+'.png' for m,w in [('organization',1440),('organization',390),('program',1440),('place',390),('staffaccessuser',390),('seoissue',320)]]
for name in screens:
    p=REPO/'output/playwright/manual-check'/name
    shutil.copyfile(p,HERE.parent/'screenshots'/name)
http=[]
for path in ['/qa/','/ru/','/ru/catalog/','/admin/login/']+['/qa/files/screens/'+n for n in screens]:
    with urllib.request.urlopen('http://127.0.0.1:8780'+path,timeout=20) as response:
        assert response.status == 200
        http.append({'url':path,'status':response.status})
info = json.loads(subprocess.check_output(['docker','inspect','kidsmap-manual-20261004'],text=True))[0]
assert info['Config']['Labels']['kidsmap.manual.owner']=='manual-20261004'
assert info['HostConfig']['NetworkMode']=='none' and not info['HostConfig']['PortBindings']
head = subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()
assert head == '015d031d8eb17114bd860159dde805b38df3c13c'
output={'status':'PASS','checked_at':datetime.now(timezone.utc).isoformat(),'head_unchanged':head,
        'source_files_worktree_runtime':len(manifest['source_files']),'changed_application_files':manifest['changed_files'],
        'previous_mapfix_runtime_unchanged':len(baseline['source_files']),
        'previous_completion_runtime_unchanged':len(old_completion['source_files']),
        'immutable_evidence':historical,'preserved_originals':len(preserved),
        'backend':{k:suite[k] for k in ['status','tests_run','failures','errors','skipped','elapsed_seconds']},
        'backend_snapshot':'backend-source-snapshot.json; final subsequent delta is CSS-only in kidsmap_changelist.css',
        'backend_final_source_delta':backend_delta,
        'browser':{'matrix':366,'mobile_components':27,'errors':matrix['errors']+mobile['errors'],'network':matrix['network']+mobile['network']},
        'data':read(HERE/'data-verification.json'),'http':http,'database_network':'none','ports_published':False,
        'production':'NOT_CONTACTED','commit_push_deploy':'NOT_RUN'}
(HERE/'final-verification.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in output.items() if k not in ['changed_application_files','http']},ensure_ascii=False))
