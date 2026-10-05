"""Verify completed independent evidence before its completion claim."""
import hashlib
import json
import sys
from pathlib import Path

root=Path('/mnt/c/kidsmap');report=root/'docs/task33/reports'
load=lambda name:json.loads((report/name).read_text())
tests=load('28-database-results.json');suite=tests['suite-results.json']
assert suite['tests_run']==32 and len(set(suite['executed_ids']))==32
assert not any(suite[key] for key in ('failures','errors','skipped'))
source=load('28-database-source.json');assert source['reviewed_source_count']==23 and source['mismatches']==0
for entry in source['source_files']:
    assert hashlib.sha256((root/entry['path']).read_bytes()).hexdigest()==entry['current_sha256']==entry['executed_sha256']
recovery=load('28-recovery-results.json');result=recovery['r2-rehearsal.json']
assert result['status']=='PASS' and result['native_pg_restore']=='PASS'
assert result['tables_compared_count']==98 and result['private_files_compared']==2
assert result['source_and_restore_row_digests_equal'] and result['media_byte_digests_equal'] and result['private_media_digests_equal']
assert result['forced_mid_batch_rollback'] and result['dry_run_read_only'] and not result['rerun_duplicate_pieces']
standby=result['compatible_standby_read'];assert standby['status']=='PASS' and standby['read_only_database']=='qa_stage28_restore'
metadata=Path(sys.argv[1]).resolve(strict=True)
assert metadata.name=='artifact.json' and metadata.is_relative_to(Path('/root/task33-evidence/stage28-artifact-20261003'))
artifact=json.loads(metadata.read_text())
assert standby['artifact_identity']==artifact['identity']
manifest=json.loads((Path(artifact['archive']).parent/'manifest.json').read_text())
inventory={row['path']:row['sha256'] for row in manifest['files']}
for entry in source['source_files']:
    assert inventory[entry['path']]==entry['current_sha256'], 'Artifact source drift'
reader=next(row for row in manifest['files'] if row['path']=='docs/task33/qa28/recovery_reader.py')
assert hashlib.sha256((root/reader['path']).read_bytes()).hexdigest()==reader['sha256']
for evidence in (tests,recovery):
    assert evidence['run.json']['status']=='PASS' and evidence['run.json']['cleanup']=='PASS'
    assert evidence['run.json']['run_root_removed'] and evidence['run.json']['socket_root_removed']
    assert evidence['isolation.json']['network_guard'] and evidence['isolation.json']['libpq_guard']
    assert not evidence['isolation.json']['external_credentials_present']
    assert evidence['migrations.json']['applied_count']==167 and evidence['migrations.json']['unapplied_count']==0
print(json.dumps({'status':'PASS','independent_cases':32,'reviewed_source':23,'recovered_tables':98,'private_files':2,'artifact':artifact['identity']}))
