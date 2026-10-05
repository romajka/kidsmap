#!/bin/bash
set -euo pipefail
stamp=$1
shift
checkout=/root/km28-db
output=/tmp/task33-qa28-db-$stamp
retained=/root/task33-evidence/$stamp
test -d "$checkout/src"
test ! -e "$output"
test ! -e "$retained"
cd "$checkout"
set +e
.venv/bin/python docs/task33/qa04/run.py --mode all --output "$output" --label catalog.testcases.test_task33_specialist_db_review --label catalog.testcases.test_task33_event_schema --label catalog.testcases.test_task33_event_concurrency --label catalog.testcases.test_task33_notifications "$@"
result=$?
set -e
mkdir -p /root/task33-evidence
if test -d "$output"; then cp -a "$output" "$retained"; fi
python3 - "$retained" <<'PY'
import json,sys
from pathlib import Path
r=Path(sys.argv[1]);result={'evidence':str(r)}
for name in ('run.json','isolation.json','migrations.json','suite-results.json'):
    p=r/name
    if p.exists():
        v=json.loads(p.read_text())
        if name=='run.json':v={k:v.get(k) for k in ('status','child_exit','cleanup','run_root_removed','socket_root_removed','exception')}
        if name=='suite-results.json':v={k:v.get(k) for k in ('tests_run','failures','errors','skipped','status','elapsed_seconds')}
        result[name]=v
print(json.dumps(result,indent=2))
PY
exit "$result"
