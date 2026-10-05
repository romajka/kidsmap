#!/bin/bash
set -euo pipefail
cd /root/task33-browser-tools
out=/mnt/c/kidsmap/scratch/final-audit-report-render.txt
npx playwright-cli -s=finalaudit-report snapshot > /mnt/c/kidsmap/scratch/final-audit-report-initial.txt
npx playwright-cli -s=finalaudit-report run-code --filename /mnt/c/kidsmap/docs/task33/final-audit/qa/report_browser.js > "$out"
python3 - <<'PY'
import json,hashlib
from pathlib import Path
raw=Path('/mnt/c/kidsmap/scratch/final-audit-report-render.txt').read_text()
assert '### Result' in raw,raw
data=json.loads(raw.split('### Result',1)[1].split('###',1)[0].strip())
assert data['status']=='PASS'
data['report_sha256']=hashlib.sha256(Path('/mnt/c/kidsmap/docs/task33/final-audit/report.html').read_bytes()).hexdigest()
data['screenshots_index_sha256']=hashlib.sha256(Path('/mnt/c/kidsmap/docs/task33/final-audit/screenshots/index.json').read_bytes()).hexdigest()
Path('/mnt/c/kidsmap/docs/task33/final-audit/report-render.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data))
PY
