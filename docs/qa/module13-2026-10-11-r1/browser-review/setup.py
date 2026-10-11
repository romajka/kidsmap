import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
REPO = HERE.parents[3]
SCRATCH = REPO / '.tmp/module13-20261011-r1/browser-review'
SCRATCH.mkdir(parents=True, exist_ok=True)
(HERE / 'screenshots').mkdir(exist_ok=True)
config = json.loads((REPO / '.tmp/module13-20261011-r1/playwright.json').read_text())
config['outputDir'] = str(SCRATCH / 'playwright')
(SCRATCH / 'playwright.json').write_text(json.dumps(config), encoding='utf-8')
print(json.dumps({'artifact_directory': str(HERE), 'scratch': str(SCRATCH), 'session': 'module13-visual'}))
