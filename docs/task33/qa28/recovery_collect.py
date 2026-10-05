"""Collect aggregate independent evidence; never copy dumps/logs/private bytes."""
import json
import sys
from pathlib import Path

raw=Path(sys.argv[1]);target=Path(sys.argv[2]);target.parent.mkdir(parents=True,exist_ok=True)
result={'raw_evidence':str(raw),'scope':'independent database reviewer; synthetic disposable only'}
for name in ('run.json','isolation.json','migrations.json','checks.json','r2-rehearsal.json','suite-results.json'):
    path=raw/name
    if not path.is_file():continue
    value=json.loads(path.read_text())
    if name=='run.json':value={k:value.get(k) for k in ('status','child_exit','cleanup','run_root_removed','socket_root_removed','exception')}
    if name=='r2-rehearsal.json':value.pop('raw_dump',None)
    result[name]=value
target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'written':str(target),'available':list(result)[2:]}))
