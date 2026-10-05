"""Collect only synthetic IDs, source references and QA safety aggregates."""
import collections,json,sys
from pathlib import Path
raw=Path(sys.argv[1]);out=Path(sys.argv[2]);kind=sys.argv[3]
root=Path(__file__).resolve().parents[4]
record={'run':raw.name,'raw_evidence':str(raw),'executor':'/root/stage28_release','scope':'fresh comprehensive audit; synthetic disposable only','production':'NOT_CONTACTED'}
fields={'run.json':['status','child_exit','cleanup','run_root_removed','socket_root_removed','exception'],
 'isolation.json':['django_testing','single_disposable_postgresql_alias','unix_connection','network_guard','libpq_guard','cache','email','media_isolated','external_credentials_present','postgresql','django','python','psycopg'],
 'migrations.json':['applied_count','unapplied_count','leaves','vendor'],
 'discovery.json':['explicit_count','explicit_unique_count','duplicate_explicit_ids'],
 'suite-results.json':['tests_run','failures','errors','skipped','elapsed_seconds','status','executed_ids','problems','problem_ids_complete']}
for name,keys in fields.items():
    if(raw/name).is_file():
        data=json.loads((raw/name).read_text());record[name]={k:data[k]for k in keys if k in data}
for name in('checks.json','r2-rehearsal.json','stage19-query-comparison.json'):
    if(raw/name).is_file():
        data=json.loads((raw/name).read_text())
        if isinstance(data,dict):data.pop('raw_dump',None)
        record[name]=data
if kind=='full':
    suite=record['suite-results.json'];ids=set(suite['executed_ids']);problems={p['id']for p in suite['problems']}
    prior=json.loads((root/'docs/task33/reports/28-full-results.json').read_text(encoding='utf8'))
    old={p['id']:p for p in prior['classification']['remaining_problem_entries']}
    taskids=sorted(i for i in ids if '.test_task33_'in i)
    record['task33']={'executed':len(taskids),'executed_ids':taskids,'failed_ids':sorted(problems&set(taskids))}
    record['comparison_to28']={'retained_ids':sorted(problems&set(old)),'not_failed_this_run':sorted(set(old)-problems),'new_ids':sorted(problems-set(old))}
    rows=[]
    for item in suite['problems']:
        previous=old.get(item['id']);row=dict(item)
        row['prior_label']=previous['classification']if previous else'UNCLASSIFIED_NEW'
        row['same_kind_exception']=bool(previous and all(item[k]==previous[k]for k in('kind','exception')))
        row['interpretation']='Prior label is navigation only; see fresh domain/security review, not proof of harmlessness.'
        rows.append(row)
    record['failure_review']={'entries':rows,'prior_label_counts':dict(collections.Counter(r['prior_label']for r in rows))}
out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'written':str(out),'run_status':record['run.json']['status'],'cleanup':record['run.json']['cleanup'],'suite':{k:record.get('suite-results.json',{}).get(k)for k in('tests_run','failures','errors','skipped')}}))
