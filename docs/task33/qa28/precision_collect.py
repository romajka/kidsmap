"""Retain TDD evidence without test records, SQL or HTML payloads."""
import hashlib
import json
from pathlib import Path
ROOT=Path('/mnt/c/kidsmap')
def collect(stamp):
    raw=Path('/root/task33-evidence')/stamp
    record={'evidence':str(raw)}
    for name,keys in{
        'suite-results.json':['tests_run','failures','errors','skipped','executed_ids','problems','status'],
        'run.json':['status','child_exit','cleanup','run_root_removed','socket_root_removed'],
        'isolation.json':['network_guard','libpq_guard','external_credentials_present'],
        'migrations.json':['applied_count','unapplied_count'],
        'discovery.json':['explicit_count','explicit_unique_count','duplicate_explicit_ids'],
    }.items():
        data=json.loads((raw/name).read_text());record[name]={k:data[k]for k in keys}
    return record
red=collect('stage28-admin-precision-red3-20261004')
first_green=collect('stage28-admin-precision-green-20261004')
publication_red=collect('stage28-admin-publication-red-20261004')
owner_red=collect('stage28-owner-precision-red3-20261004')
green=collect('stage28-admin-precision-final-green-20261004')
assert red['suite-results.json']['tests_run']==2 and red['suite-results.json']['failures']==1 and red['suite-results.json']['errors']==0
assert publication_red['suite-results.json']['tests_run']==3 and publication_red['suite-results.json']['failures']==1 and publication_red['suite-results.json']['errors']==0
assert owner_red['suite-results.json']['tests_run']==2 and owner_red['suite-results.json']['failures']==1 and owner_red['suite-results.json']['errors']==0
assert green['suite-results.json']['tests_run']==43 and not any(green['suite-results.json'][k]for k in('failures','errors','skipped'))
for record in(red,first_green,publication_red,owner_red,green):
    assert record['run.json']['cleanup']=='PASS'
    assert record['run.json']['run_root_removed'] and record['run.json']['socket_root_removed']
    assert record['isolation.json']['network_guard'] and record['isolation.json']['libpq_guard']
    assert not record['isolation.json']['external_credentials_present']
sources=[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()}for p in(
    'src/catalog/domain_admin/place.py','src/catalog/forms.py','src/catalog/testcases/test_task33_event_admin_precision.py')]
out={'status':'PASS_RED_THEN_GREEN','red':red,'first_green':first_green,'publication_red':publication_red,'owner_red':owner_red,'green':green,'source_artifacts':sources,
 'scope':'EventAdminForm preserves start/end/publication precision only for unchanged displayed minute; changed occurrence requires guarded service.',
 'assertions_weakened':False,'production':'NOT_CONTACTED',
 'earlier_harness_failures':['First RED invocation missing --label rejected before DB.',
 'RED2 helper imported TestCase directly and module selected69cases; two precision cases gave expected1red/1pass. Module import alias corrected; RED3 selected2cases only.',
 'Initial owner test asserted form-level rejection although occurrence validation belongs to save service; moved to actual controller. Published owner fixture is not editable; corrected to approved occurrence returned to draft. These preliminary failed test drafts retained separately, not counted as meaningful RED acceptance.']}
(ROOT/'docs/task33/reports/28-precision-results.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':out['status'],'red_cases':2,'publication_red_cases':3,'owner_red_cases':2,'green_cases':43,'source':sources}))
