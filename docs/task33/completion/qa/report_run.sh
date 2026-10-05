#!/bin/bash
set -euo pipefail
evidence=/root/task33-evidence/completion-report-c1
test ! -e "$evidence"
mkdir -p "$evidence"
cd /root/task33-browser-tools
export PATH=/root/task33-browser-tools/node_modules/.bin:$PATH
trap 'npx playwright-cli -s=completion-report close > "$evidence/close.log" 2>&1 || true' EXIT
npx playwright-cli -s=completion-report open about:blank > "$evidence/open.log"
sed "s|__REPORT_EVIDENCE__|$evidence|g" /mnt/c/kidsmap/docs/task33/completion/qa/report_browser.js > "$evidence/matrix.js"
npx playwright-cli -s=completion-report run-code --filename "$evidence/matrix.js" > "$evidence/result-cli.txt"
npx playwright-cli -s=completion-report console error > "$evidence/console-cli.txt"
python3 - <<'PY'
import hashlib,json,shutil
from pathlib import Path
source=Path('/root/task33-evidence/completion-report-c1')
out=Path('/mnt/c/kidsmap/docs/task33/completion/report-checks');out.mkdir(exist_ok=False)
raw=(source/'result-cli.txt').read_text()
assert '### Result' in raw,raw[:2000]
result=json.loads(raw.split('### Result',1)[1].split('###',1)[0].strip())
assert result['status']=='PASS' and not result['errors']
result['raw_evidence']=str(source)
result['html_sha256']=hashlib.sha256((out.parent/'report.html').read_bytes()).hexdigest()
result['screenshots']=[]
for name in ('report-390.png','report-1440.png'):
    shutil.copyfile(source/name,out/name)
    result['screenshots'].append({'path':name,'sha256':hashlib.sha256((out/name).read_bytes()).hexdigest()})
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
PY
