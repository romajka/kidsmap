"""Export only allowlisted synthetic aggregate evidence; never include logs/env."""
import json
from pathlib import Path
roots=Path('/root/task33-evidence')
keys={
 'suite-results.json':['tests_run','failures','errors','skipped','status','problems'],
 'run.json':['status','child_exit','cleanup','run_root_removed','socket_root_removed'],
 'migrations.json':['applied_count','unapplied_count'],
 'discovery.json':['explicit_count','explicit_unique_count','duplicate_explicit_ids'],
}
runs=[]
for source in sorted(roots.glob('stage27-*')):
    if not source.is_dir():continue
    run={'stamp':source.name,'evidence':str(source)}
    for name,allow in keys.items():
        if (source/name).is_file():
            data=json.loads((source/name).read_text())
            run[name]={key:data[key] for key in allow if key in data}
    runs.append(run)
Path('/mnt/c/kidsmap/docs/task33/reports/27-runtime-history.json').write_text(
    json.dumps({'stage':27,'runs':runs},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'runs':len(runs)}))
