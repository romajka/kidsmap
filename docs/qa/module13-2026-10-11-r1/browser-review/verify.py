import ast
import collections
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.stdout.reconfigure(encoding='utf-8')
issues = []
report_file = HERE / 'verification.json'
report_file.write_text('{}', encoding='utf-8')
for path in HERE.glob('*.py'):
    try:
        ast.parse(path.read_text(encoding='utf-8'))
    except Exception as e:
        issues.append({'file': path.name, 'syntax_error': str(e)})
script = "const fs=require('fs'),vm=require('vm');const p=process.argv[1];for(const f of fs.readdirSync(p).filter(f=>f.endsWith('.js'))){let s=fs.readFileSync(p+'/'+f,'utf8');if(f==='common.js')s='async original=>{'+s+'}';new vm.Script('('+s+')');}process.stdout.write('JS syntax PASS');"
js = subprocess.run(['C:/Program Files/nodejs/node.exe', '-e', script, str(HERE)], capture_output=True, text=True, encoding='utf-8')
if js.returncode:
    issues.append({'js_syntax': js.stderr[:700]})
matrix = json.loads((HERE / 'matrix.json').read_text(encoding='utf-8'))
counts = json.loads((HERE / 'counts.json').read_text(encoding='utf-8'))
actual_counts = dict(collections.Counter(r['status'] for r in matrix['rows']))
if actual_counts != counts['counts']:
    issues.append({'counts_mismatch': True})
observations = json.loads((HERE / 'observations.json').read_text(encoding='utf-8'))
for role in ['guest', 'owner', 'admin']:
    cells = {(o['lang'], o['width']) for o in observations if o['role'] == role}
    expected = {(lang, width) for lang in ['ru', 'az', 'en'] for width in [360,390,768,1024,1280,1440]}
    if cells != expected:
        issues.append({'role': role, 'missing_cells': list(expected - cells)})
    mismatches = [o['url'] for o in observations if o['role'] == role and o['geometry']['htmlLang'] != o['lang']]
    if mismatches:
        issues.append({'language_mismatch': mismatches})
manifest = json.loads((HERE / 'screenshot-manifest.json').read_text())
for entry in manifest:
    path = HERE / entry['file']
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
        issues.append({'bad_screenshot_hash': entry['file']})
    with Image.open(path) as im:
        if im.size != (entry['pixel_width'], entry['pixel_height']):
            issues.append({'bad_screenshot_size': entry['file']})
        im.verify()
credential = (REPO / '.tmp/module13-20261011-r1/credential').read_text()
for path in HERE.rglob('*'):
    if not path.is_file() or path.suffix.lower() not in ['.py','.js','.json','.jsonl','.txt','.csv','.md']:
        continue
    content = path.read_text(encoding='utf-8', errors='replace')
    if credential in content:
        issues.append({'credential_leak': path.relative_to(HERE).as_posix()})
    if path.suffix == '.md':
        for link in re.findall(r'\]\(([^)]+)\)', content):
            if not link.startswith(('http:', 'https:', '#')):
                if not (path.parent / link.split('#')[0]).exists():
                    issues.append({'broken_link': link, 'file': path.name})
with urllib.request.urlopen('http://localhost:8831/qa/version/', timeout=15) as response:
    version = json.load(response)
if not version['testing'] or not version['entry_matches_startup'] or not version['startup_matches_disk']:
    issues.append({'runtime_attestation_failed': True})
report = {'exit_code': 1 if issues else 0, 'counts': actual_counts, 'page_observations': len(observations), 'cells_per_role': counts['cells_per_role'], 'native_png_complete': counts['native_png_complete'], 'native_png_retained': len(manifest), 'derived_contacts': counts['derived_contacts'], 'credential_scan': 'PASS' if not any('credential_leak' in i for i in issues) else 'FAIL', 'javascript_syntax_exit': js.returncode, 'runtime_version': version, 'issues': issues}
report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
sys.exit(report['exit_code'])
