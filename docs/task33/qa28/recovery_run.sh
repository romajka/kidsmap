#!/bin/bash
set -euo pipefail
stamp=$1
artifact=${2:-}
checkout=/root/km28-db
source_checkout=/mnt/c/kidsmap
output=/tmp/task33-qa28-db-$stamp
retained=/root/task33-evidence/$stamp
test ! -e "$output"
test ! -e "$retained"
python3 - <<'PY'
from pathlib import Path
import hashlib,shutil,json
source=Path('/mnt/c/kidsmap');target=Path('/root/km28-db');target.mkdir(exist_ok=True)
entries=[]
for scope in ('src','config','catalog','static','templates','locale','docs/task33/qa04','docs/task33/qa23','docs/task33/qa28'):
    for src in (source/scope).rglob('*'):
        if src.is_symlink(): raise RuntimeError('Source symlink forbidden')
        if not src.is_file() or '__pycache__' in src.parts or src.suffix=='.pyc':continue
        name=src.relative_to(source);dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        entries.append({'path':name.as_posix(),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
for name in ('manage.py','requirements.txt'):
    shutil.copy2(source/name,target/name)
(target/'recovery-source.json').write_text(json.dumps(entries))
venv=target/'.venv'
if not venv.exists(): venv.symlink_to('/root/kidsmap-task33/.venv',target_is_directory=True)
print('Independent application source freeze; environment/DB/media/git excluded')
PY
cd "$checkout"
env -i PATH=/usr/bin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 .venv/bin/python -m django compilemessages --locale az --locale ru --locale en --ignore .venv --ignore scratch
service docker start >/dev/null
set +e
TASK33_R1_ARTIFACT_JSON="$artifact" .venv/bin/python docs/task33/qa28/recovery_run.py --mode probe --output "$output"
result=$?
set -e
mkdir -p /root/task33-evidence
if test -d "$output"; then cp -a "$output" "$retained"; fi
cp recovery-source.json "$retained/source.json"
python3 - "$retained" <<'PY'
import json,sys
from pathlib import Path
r=Path(sys.argv[1]);result={'evidence':str(r)}
for name in ('run.json','isolation.json','migrations.json','r2-rehearsal.json'):
    p=r/name
    if p.exists():
        value=json.loads(p.read_text())
        if name=='run.json':value={k:value.get(k) for k in ('status','child_exit','cleanup','run_root_removed','socket_root_removed','exception')}
        result[name]=value
print(json.dumps(result,indent=2))
PY
exit "$result"
