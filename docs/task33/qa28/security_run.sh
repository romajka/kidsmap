#!/bin/bash
set -euo pipefail
checkout=/root/km28-security
source_checkout=/mnt/c/kidsmap
mode=$1
stamp=$2
shift 2
output=/tmp/task33-stage28-security-$stamp
retained=/root/task33-evidence/$stamp
test ! -e "$output"
test ! -e "$retained"
python3 - <<'PY'
from pathlib import Path
import shutil, subprocess
source=Path('/mnt/c/kidsmap'); target=Path('/root/km28-security')
target.mkdir(exist_ok=True)
if not (target/'.venv').exists(): (target/'.venv').symlink_to('/root/kidsmap-task33/.venv', target_is_directory=True)
scopes=['src','config','catalog','manage.py','requirements.txt','Dockerfile','static','templates','locale','docs/task33/qa04','docs/task33/qa08','docs/task33/qa10','docs/task33/qa23','docs/task33/qa24','docs/task33/qa25','docs/task33/qa26','docs/task33/qa27','docs/task33/qa28']
tracked=subprocess.check_output(['git','ls-files','-z','--',*scopes],cwd=source)
added=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z','--','src','static','locale','docs/task33/qa23','docs/task33/qa24','docs/task33/qa25','docs/task33/qa26','docs/task33/qa25','docs/task33/qa26','docs/task33/qa27','docs/task33/qa28'],cwd=source)
for raw in sorted(set((tracked+added).split(b'\0'))):
    if not raw: continue
    path=raw.decode(); src=source/path; dst=target/path
    if src.is_symlink() or not src.is_file(): raise RuntimeError('Unverified source file')
    if not dst.resolve().is_relative_to(target): raise RuntimeError('Unsafe mirror target')
    dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
print('Windows source mirrored to isolated Linux checkout; no env/DB/media/git copied')
PY
cd "$checkout"
env -i PATH=/usr/bin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 .venv/bin/python -m django compilemessages --locale az --locale ru --locale en --ignore .venv --ignore scratch
if [[ "$stamp" == *release3* ]]; then
    .venv/bin/python /mnt/c/kidsmap/docs/task33/qa28/security_snapshot.py release3
fi

set +e
.venv/bin/python docs/task33/qa04/run.py --mode "$mode" --output "$output" "$@"
result=$?
set -e
mkdir -p /root/task33-evidence
if test -d "$output"; then cp -a "$output" "$retained"; fi
if [[ "$stamp" == *release3* ]]; then
    .venv/bin/python /mnt/c/kidsmap/docs/task33/qa28/security_snapshot.py release3
fi
python3 - "$retained" <<'PY'
from pathlib import Path
import sys,json
out=Path(sys.argv[1]); result={'evidence':str(out)}
for file,keys in [('run.json',['status','child_exit','cleanup','run_root_removed','socket_root_removed','exception']),('isolation.json',['postgresql','django','python','psycopg','network_guard','libpq_guard','external_credentials_present']),('discovery.json',['explicit_count','explicit_unique_count','duplicate_explicit_ids']),('migrations.json',['applied_count','unapplied_count']),('suite-results.json',['tests_run','failures','errors','skipped','status'])]:
    if (out/file).exists():
        data=json.loads((out/file).read_text());result[file]={key:data[key] for key in keys if key in data}
if (out/'checks.json').exists(): result['checks']=json.loads((out/'checks.json').read_text())
print(json.dumps(result,indent=2))
PY
exit "$result"
