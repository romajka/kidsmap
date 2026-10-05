"""Keep only synthetic test identities and safety aggregates from isolated QA04."""
import json,sys
from pathlib import Path
raw=Path(sys.argv[1]);out=Path(sys.argv[2]);workspace=Path(sys.argv[3])
record={'stage':28,'evidence':str(raw),'scope':'CURRENT_FULL_EXPLICIT_POSTGRESQL'}
fields={
 'suite-results.json':['tests_run','failures','errors','skipped','elapsed_seconds','status','executed_ids','problems','problem_ids_complete'],
 'run.json':['status','child_exit','cleanup','run_root_removed','socket_root_removed'],
 'isolation.json':['postgresql','django','python','psycopg','network_guard','libpq_guard','external_credentials_present'],
 'discovery.json':['explicit_count','explicit_unique_count','duplicate_explicit_ids'],
 'migrations.json':['applied_count','unapplied_count']}
for name,keys in fields.items():
    d=json.loads((raw/name).read_text());record[name]={k:d[k]for k in keys if k in d}
record['checks.json']=json.loads((raw/'checks.json').read_text())
suite=record['suite-results.json'];executed=set(suite['executed_ids']);problem_ids={p['id']for p in suite['problems']}
prior=json.loads((workspace/'docs/task33/reports/27-results.json').read_text())['suite-results.json']
required=set(prior['executed_ids']);current={i for i in executed if '.test_task33_' in i}
assert required<=executed,'Some prior Task33 cases not executed'
record['task33_subset']={'executed':len(current),'prior27_expected':len(required),
                       'missing_expected':sorted(required-executed),'failed_ids':sorted(current&problem_ids),
                       'status':'PASS'if not current&problem_ids else'FAIL'}
old=json.loads((workspace/'docs/task33/reports/24-results.json').read_text())['classification']['remaining_problem_entries']
oldids={p['id']for p in old}
record['baseline_comparison']={'prior24_problem_ids':len(oldids),'current_problem_ids':len(problem_ids),
                              'retained_ids':sorted(oldids&problem_ids),'resolved_ids':sorted(oldids-problem_ids),
                              'new_ids_require_source_classification':sorted(problem_ids-oldids)}
out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'full':{k:suite[k]for k in ['tests_run','failures','errors','skipped','status']},
                  'task33_subset':record['task33_subset'],'new_problem_ids':record['baseline_comparison']['new_ids_require_source_classification']}))
