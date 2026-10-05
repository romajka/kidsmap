#!/bin/bash
set -euo pipefail
stamp=$1
artifact=${2:-}
checkout=/root/kidsmap-task33
source_checkout=/mnt/c/kidsmap
output=/tmp/task33-qa23-$stamp
retained=/root/task33-evidence/qa23-$stamp
test ! -e "$output"
test ! -e "$retained"
test -d "$checkout/.venv"
mkdir -p "$checkout/docs/task33/qa23"
cp -a "$source_checkout/docs/task33/qa23/." "$checkout/docs/task33/qa23/"
cd "$checkout"
service docker start >/dev/null
set +e
if test -n "$artifact"; then
  TASK33_R1_ARTIFACT_JSON="$artifact" .venv/bin/python docs/task33/qa23/rehearsal.py --mode probe --output "$output"
else
  .venv/bin/python docs/task33/qa23/rehearsal.py --mode probe --output "$output"
fi
result=$?
set -e
mkdir -p /root/task33-evidence
if test -d "$output"; then cp -a "$output" "$retained"; fi
python3 - "$retained" <<'PY'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); summary={'evidence':str(root)}
for name in ('run.json','r1-rehearsal.json'):
    path=root/name
    if path.exists():
        value=json.loads(path.read_text())
        if name=='run.json':
            value={key:value.get(key) for key in ('status','child_exit','cleanup','run_root_removed','socket_root_removed','exception')}
        summary[name]=value
print(json.dumps(summary,indent=2))
PY
exit "$result"
