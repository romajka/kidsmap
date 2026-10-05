"""Fail-closed acceptance of retained final executions and preserved entry files."""
import hashlib,json,subprocess
from pathlib import Path

ROOT=Path('/mnt/c/kidsmap');OUT=ROOT/'docs/task33/completion'
RAW=Path('/root/task33-evidence')
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
host=read(OUT/'runs/full-host-final-c2.json')
image_root=RAW/'completion-image-c2'
image={name:read(image_root/(name+'.json')) for name in ('run','suite-results','image-runtime','isolation','migrations','checks','discovery')}
for suite in (host['suite'],image['suite-results']):
    assert suite['tests_run']==1844 and suite['failures']==suite['errors']==suite['skipped']==0
    assert len(set(suite['executed_ids']))==1844 and not suite['problems']
assert set(host['suite']['executed_ids'])==set(image['suite-results']['executed_ids'])
assert image['run']['status']==image['run']['cleanup']=='PASS'
assert host['run']['status']==host['run']['cleanup']=='PASS' and not host['frozen_source_changed']
assert image['image-runtime']['image_source_match'] and not image['image-runtime']['application_code_mount']
for directory in (RAW/'completion-full-host-final-c2',image_root):
    assert all(check['status']=='PASS' and check['exit']==0 for check in read(directory/'checks.json'))
    migrations=read(directory/'migrations.json');assert migrations['applied_count']==168 and migrations['unapplied_count']==0
    isolation=read(directory/'isolation.json')
    assert all(isolation[key] for key in ('django_testing','single_disposable_postgresql_alias','unix_connection','network_guard','libpq_guard','media_isolated'))
    assert not isolation['external_credentials_present']
old_image='sha256:6566a67c0b3ab3da8ea040314b016908b1cbe17e09a50912fc5c80fe5228f5fd'
assert subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',old_image],text=True).strip()==old_image
write('runs/image-final-c2.json',{'raw_evidence':str(image_root),**image})
recovery_root=RAW/'completion-recovery-c6'
recovery={name:read(recovery_root/(name+'.json')) for name in ('run','r2-rehearsal','source','isolation','migrations','checks')}
assert recovery['run']['status']==recovery['run']['cleanup']==recovery['r2-rehearsal']['status']=='PASS'
assert not recovery['source']['frozen_source_changed']
artifact=read(OUT/'artifact.json')
assert recovery['r2-rehearsal']['compatible_standby_read']['artifact_identity']==artifact['identity']
assert image['image-runtime']['image_id']==artifact['image_id']
write('recovery-results.json',{'raw_evidence':str(recovery_root),**{k:v for k,v in recovery.items() if k!='source'},
    'harness_source_sha256':sha(recovery_root/'source.json'),
    'schema_comparison':'Exact columns, constraints and indexes after narrowly canonicalizing equivalent constant varchar-array-to-text casts; raw structural metadata retained.',
    'normalization_negative_checks':['changed primary-key column rejected','changed index predicate rejected']})
browser=read(OUT/'browser-results.json');assert browser['status']=='PASS' and browser['contexts']==861
jslog=(OUT/'js-final.log').read_text(encoding='utf-8-sig')
assert all(value in jslog for value in ('tests 30','pass 30','fail 0','skipped 0','cancelled 0'))
ledger=read(OUT/'regression-ledger.json');assert ledger['host_pass']==ledger['image_pass']==120
entry=read(OUT/'entry.json');backup=ROOT/'scratch'/Path(entry['snapshot'].replace('\\','/')).name/'files'
assert all(sha(backup/r['path'])==r['sha256'] for r in entry['files'])
assert all(sha(ROOT/r['path'])==r['sha256'] for r in entry['immutable_audit'])
assert not [r['path'] for r in entry['files'] if not (ROOT/r['path']).exists()]
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==entry['head']
host_source=read(RAW/'completion-full-host-final-c2/source.json')
performance=read(RAW/'completion-full-host-final-c2/stage19-query-comparison.json')
assert performance['batch_one']['queries']==performance['batch_eight']['queries']
write('performance-results.json',{'host_cards':performance,'native_event_control':recovery['r2-rehearsal']['performance'],
    'meaning':'Local synthetic query-count comparison, not a production load test; per-card control may use current unbatched reader.'})
host_map={r['path']:r['sha256'] for r in host_source['files']}
manifest=read(Path(artifact['archive']).parent/'manifest.json')
artifact_map={r['path']:r['sha256'] for r in manifest['files']}
app={}
for domain in ('src','templates','static','locale','config','scripts'):
    for path in (ROOT/domain).rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix not in ('.pyc','.mo'):
            app[path.relative_to(ROOT).as_posix()]=sha(path)
app['manage.py']=sha(ROOT/'manage.py')
assert all(host_map.get(k)==v for k,v in app.items()),'Host/current APP mismatch'
assert all(artifact_map.get(k)==v for k,v in app.items()),'Artifact/current APP mismatch'
screens=read(OUT/'screenshots/index.json')
assert screens['count']==30 and all(sha(OUT/r['path'])==r['sha256'] for r in screens['screenshots'])
result={'status':'PASS','run':entry['run'],'head_unchanged':entry['head'],
    'entry_backup_files_verified':len(entry['files']),'entry_paths_deleted':0,
    'immutable_audit_files_verified':len(entry['immutable_audit']),
    'current_host_image_browser_application_files':len(app),'same_application_source':True,
    'host_tests':1844,'image_tests':1844,'failures':0,'errors':0,'skipped':0,
    'baseline_problem_entries_host_and_image_pass':120,'baseline_unique_test_ids':109,
    'migrations_applied':168,'migrations_unapplied':0,'django_checks_and_guards':'PASS','historical_image_preserved':old_image,
    'browser_contexts':861,'browser_checks':browser['checks'],'browser_unexpected_errors':0,
    'screenshots_verified':30,'recovery':'PASS','image_id':artifact['image_id'],
    'javascript_tests':30,'javascript_log_sha256':sha(OUT/'js-final.log'),
    'artifact_identity':artifact['identity'],'production':'NOT_CONTACTED','commit_push_deploy':'NOT_RUN',
    'source_files':[{'path':k,'sha256':v} for k,v in sorted(app.items())]}
write('final-verification.json',result)
print(json.dumps({k:v for k,v in result.items() if k!='source_files'}))
