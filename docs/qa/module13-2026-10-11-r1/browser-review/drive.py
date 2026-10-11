import datetime
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
REPO = HERE.parents[3]
sys.stdout.reconfigure(encoding='utf-8')
credential = (REPO / '.tmp/module13-20261011-r1/credential').read_text()
source = (HERE / sys.argv[1]).read_text(encoding='utf-8')
source = source.replace('__VISUAL_COMMON__', (HERE / 'common.js').read_text(encoding='utf-8'))
source = source.replace('__FIXTURES_JSON__', (RUN / 'fixtures.json').read_text())
source = source.replace('__CARD_URLS__', (RUN / 'card-urls.json').read_text())
source = source.replace('__ROLE__', sys.argv[2] if len(sys.argv) > 2 else 'guest')
source = source.replace('__LANG__', sys.argv[3] if len(sys.argv) > 3 else 'ru')
suffix = '-' + '-'.join(sys.argv[2:]) if len(sys.argv) > 2 else ''
(HERE / (Path(sys.argv[1]).stem + suffix + '.effective.js')).write_text(source, encoding='utf-8')
source = source.replace('__LOCAL_PASSWORD__', credential)
cli = Path.home() / 'AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js'
started = time.monotonic()
result = subprocess.run(['C:/Program Files/nodejs/node.exe', str(cli), '-s=module13-visual', 'run-code', source], capture_output=True, text=True, encoding='utf-8', errors='replace')
match = re.search(r'### Result\s*\n(.*?)(?=\n### |\Z)', result.stdout, re.S)
clean = match.group(1) if match else re.sub(r'```js.*?```', '[executed code omitted]', result.stdout, flags=re.S)
clean = clean.replace(credential, '[REDACTED]')
target = HERE / (Path(sys.argv[1]).stem + suffix + '.result.json')
if target.exists():
    attempt = 1
    while target.with_name(target.stem + f'.attempt{attempt}.json').exists():
        attempt += 1
    target.rename(target.with_name(target.stem + f'.attempt{attempt}.json'))
target.write_text(clean, encoding='utf-8')
with (HERE / 'command-ledger.jsonl').open('a', encoding='utf-8') as ledger:
    ledger.write(json.dumps({'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': '.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/browser-review/drive.py ' + ' '.join(sys.argv[1:]), 'cli_exit_code': result.returncode, 'duration_seconds': round(time.monotonic() - started, 2), 'session': 'module13-visual', 'result': target.name}) + '\n')
try:
    data = json.loads(clean)
    print(json.dumps({'keys': list(data), 'rows': len(data.get('rows', [])), 'counts': {s: sum(r.get('status') == s for r in data.get('rows', [])) for s in ['PASS', 'FAIL', 'NOT RUN']}, 'failures': [r for r in data.get('rows', []) if r.get('status') == 'FAIL'][:5]}, ensure_ascii=False)[:5000])
except ValueError:
    print(clean[:1500])
print('CLI exit', result.returncode)
sys.exit(result.returncode)
