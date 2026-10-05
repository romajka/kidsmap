#!/bin/bash
set -euo pipefail
stamp=${1:?unique run stamp required}
[[ "$stamp" =~ ^[a-zA-Z0-9-]+$ ]]
checkout=/root/km25-security
output=/tmp/task33-stage25-security-$stamp
retained=/root/task33-evidence/security25-$stamp
test ! -e "$output"
test ! -e "$retained"
mkdir -p "$checkout"
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess
source=Path('/mnt/c/kidsmap'); target=Path('/root/km25-security')
scopes=['src','config','catalog','manage.py','requirements.txt','Dockerfile','static','templates','locale','docs/task33/qa04']
tracked=subprocess.check_output(['git','ls-files','-z','--',*scopes],cwd=source)
added=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z','--','src','static','locale','docs/task33/qa04'],cwd=source)
manifest={}
for raw in sorted(set((tracked+added).split(b'\0'))):
    if not raw: continue
    path=raw.decode(); src=source/path; dst=target/path
    if src.is_symlink() or not src.is_file(): raise RuntimeError('Unverified source file')
    if not dst.resolve().is_relative_to(target): raise RuntimeError('Unsafe mirror target')
    dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
    manifest[path]=hashlib.sha256(dst.read_bytes()).hexdigest()
(target/'security-source-sha256.json').write_text(json.dumps(manifest,indent=2))
print('Independent allowlisted frozen source; no environment, working DB/media or Git copied')
PY
test -e "$checkout/.venv" || ln -s /root/kidsmap-task33/.venv "$checkout/.venv"
cd "$checkout"
set +e
env -i PATH=/usr/bin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 .venv/bin/python docs/task33/qa04/run.py --mode all --output "$output" --label catalog.testcases.test_task33_specialist_screens_security
result=$?
set -e
mkdir -p "$retained"
cp -r "$output/." "$retained/"
cp "$checkout/security-source-sha256.json" "$retained/"
exit "$result"
