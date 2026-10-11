"""Verify own report links, result counts, syntax and credential non-disclosure."""
import ast
import json
import re
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
results = {name: json.loads((HERE / (name + '.json')).read_text()) for name in (
    'primary', 'supplement-attempt1', 'supplement', 'fault-confirmed', 'private-origin',
    'ai-js', 'phone-dom', 'phone-dom-attempt1', 'fault-confirmed-environment-attempt1')}
assert results['primary']['test_count'] == 60 and results['primary']['passed'] == 60
assert results['supplement']['test_count'] == 9 and results['supplement']['passed'] == 4 and results['supplement']['failures'] == 5
assert results['phone-dom']['tests'] == 4 and results['phone-dom']['pass'] == 4
assert results['ai-js']['exit_code'] == 0
for name in ('primary', 'supplement', 'fault-confirmed', 'private-origin', 'supplement-attempt1'):
    value = results[name]
    assert value['test_count'] == sum(value[key] for key in ('passed', 'failures', 'errors', 'skipped'))
missing = []
report = (HERE / 'REPORT.md').read_text(encoding='utf-8')
for target in re.findall(r'\]\(([^)]+)\)', report):
    if not (HERE / target).exists():
        missing.append(target)
assert not missing, 'Missing report evidence link'
syntax_files = []
for path in HERE.glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'), filename=path.name)
    syntax_files.append(path.name)
secret = (ROOT / '.tmp/module12-20261011-r1/credential').read_text().strip()
secret_hits = []
for path in HERE.glob('*'):
    if path.is_file() and path.suffix in ('.py', '.md', '.json', '.log'):
        if secret and secret in path.read_text(encoding='utf-8'):
            secret_hits.append(path.name)
assert not secret_hits, 'QA credential literal leaked into own artifacts'
snapshot = json.loads((HERE / 'source-snapshot.json').read_text())
assert all(x['unchanged_HEAD'] for x in snapshot['relevant_source'].values())
completed = [results[x] for x in ('primary', 'supplement-attempt1', 'fault-confirmed', 'private-origin', 'supplement')]
record = {
    'verification_exit': 0, 'syntax_files': syntax_files, 'missing_links': missing,
    'credential_literal_hits': secret_hits, 'source_files_unchanged_HEAD': len(snapshot['relevant_source']),
    'canonical_unique_django': {'tests': 69, 'passed': 64, 'failed': 5, 'errors': 0},
    'raw_completed_django_methods_including_replays': {
        'tests': sum(x['test_count'] for x in completed), 'passed': sum(x['passed'] for x in completed),
        'failed': sum(x['failures'] for x in completed), 'errors': sum(x['errors'] for x in completed)},
    'excluded_raw_assertion': 'One initial PASS used a non-invoked fault injector; final corrected method FAIL',
    'phone_unique_dom_tests': {'tests': 4, 'passed': 4},
    'ai_js_assertion_scripts': {'scripts': 1, 'passed': 1},
    'environment_attempts': ['phone outer wrapper Unicode error after Node exit0', 'stdlib inspect shadow before Django setup'],
    'browser': 'NOT RUN by specialist; root-owned native evidence', 'external_ga': 'NOT RUN',
}
(HERE / 'verification.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
