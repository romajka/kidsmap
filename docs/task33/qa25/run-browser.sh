#!/bin/bash
set -euo pipefail
stamp=${1:?Unique evidence stamp required}
[[ "$stamp" =~ ^[a-zA-Z0-9-]+$ ]]
evidence=/root/task33-evidence/stage25-design-$stamp
test ! -e "$evidence"
mkdir -p "$evidence"
cd /root/task33-browser-tools
export PATH=/root/task33-browser-tools/node_modules/.bin:$PATH
/root/kidsmap-task33/.venv/bin/python /mnt/c/kidsmap/docs/task33/qa25/preview.py --port 8795 > "$evidence/server.log" 2>&1 &
server_pid=$!
finish() {
 npx playwright-cli -s=qa25 close > "$evidence/close-cli.txt" 2>&1 || true
 kill "$server_pid" 2>/dev/null || true
 wait "$server_pid" 2>/dev/null || true
}
trap finish EXIT
for i in $(seq 1 30); do
 if curl --max-time 2 -fsS http://127.0.0.1:8795/docs/task33/design/specialist/index.html >/dev/null; then break;fi
 if ! kill -0 "$server_pid" 2>/dev/null;then exit 2;fi
 sleep 1
done
npx playwright-cli -s=qa25 open about:blank > "$evidence/open-cli.txt"
npx playwright-cli -s=qa25 snapshot > "$evidence/initial-snapshot.txt"
python3 - "$evidence" "${2:-/mnt/c/kidsmap/docs/task33/qa25/browser-matrix.js}" <<'PY'
from pathlib import Path
import json,sys,hashlib
evidence=Path(sys.argv[1]);design=Path('/mnt/c/kidsmap/docs/task33/design/specialist')
files=sorted(p.name for p in design.glob('*.html'))
if len(files)!=8: raise SystemExit('Expected eight Specialist design HTML entry points')
source=Path(sys.argv[2]).read_text()
(evidence/'matrix.js').write_text(source.replace('__QA25_EVIDENCE__',str(evidence)).replace('__QA25_FILES__',json.dumps(files)))
snapshot=[{'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(design.iterdir()) if p.is_file()]
(evidence/'source-snapshot.json').write_text(json.dumps(snapshot,indent=2))
PY
npx playwright-cli -s=qa25 run-code --filename "$evidence/matrix.js" > "$evidence/result-cli.txt"
npx playwright-cli -s=qa25 snapshot > "$evidence/final-snapshot.txt"
npx playwright-cli -s=qa25 console error > "$evidence/console-cli.txt"
npx playwright-cli -s=qa25 requests > "$evidence/requests-cli.txt"
python3 /mnt/c/kidsmap/docs/task33/qa25/collect.py "$evidence"
