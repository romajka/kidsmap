"""Run bounded DOM baseline without Django/DB/service credentials."""
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ledger = []


def run(argv, *, env=None, output=None):
    result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8')
    row = {'argv': argv, 'cwd': str(ROOT), 'exit_code': result.returncode}
    if output:
        (HERE / output).write_text(result.stdout + result.stderr, encoding='utf-8')
        row['output_file'] = output
    else:
        row.update(stdout=result.stdout, stderr=result.stderr)
    ledger.append(row)
    (HERE / 'command-ledger.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in ledger), encoding='utf-8')
    return result


head = run(['git', 'rev-parse', 'HEAD']).stdout.strip()
branch = run(['git', 'branch', '--show-current']).stdout.strip()
status = run(['git', 'status', '--short']).stdout.splitlines()
assert run(['git', 'diff', '--exit-code', '--stat', 'HEAD', '--', 'src', 'static', 'config', 'locale']).returncode == 0
active = next(x for x in (ROOT / 'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if x.startswith('active_run:'))
files = ['static/js/location_resolution.js', 'static/js/owner_place_continuous.js',
         'src/catalog/templates/includes/location_resolution.html',
         'src/catalog/services/location_assignment.py', 'src/catalog/services/locations.py',
         'scripts/test_location_resolution.cjs', 'docs/qa/module-acceptance-prompts.md',
         'docs/superpowers/plans/2026-10-10-place-qa01-rejection-feedback.md',
         'docs/superpowers/plans/2026-10-10-place-qa02-map-fallback.md',
         'docs/superpowers/plans/2026-10-10-place-qa03-pricing-rebase.md']
before = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}
qa_env = {k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','TEMP','TMP','PATH','PATHEXT','COMSPEC'}}
qa_env.update(DJANGO_TESTING='1', KIDSMAP_JSDOM=str(ROOT / '.tmp/phone-dom/node_modules/jsdom'))
node = r'C:\Program Files\nodejs\node.exe'
version = run([node, '--version'], env=qa_env).stdout.strip()
baseline = run([node, '--test', str(HERE / 'baseline-district.cjs')], env=qa_env, output='baseline-district.txt')
existing = run([node, '--test', 'scripts/test_location_resolution.cjs'], env=qa_env, output='existing-resolver-tests.txt')
after = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}
snapshot = {'recorded_at_utc': datetime.now(timezone.utc).isoformat(), 'head': head, 'branch': branch,
    'entry_worktree': status, 'active_run': active, 'source_before_sha256': before,
    'source_after_sha256': after, 'preserved': before == after, 'node': version,
    'baseline_exit_code': baseline.returncode, 'existing_suite_exit_code': existing.returncode,
    'isolation': {'DJANGO_TESTING': True, 'django_loaded': False, 'database_used': False,
                  'external_requests': False, 'resolver_fetch': 'local promise stub'},
    'browser': 'NOT RUN', 'db_save_reload': 'NOT RUN', 'application_implementation': 'NOT AUTHORIZED'}
(HERE / 'snapshot.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
assert before == after
assert baseline.returncode == 1 and existing.returncode == 0
print(json.dumps({'baseline_exit_code': baseline.returncode, 'existing_suite_exit_code': existing.returncode,
                  'preserved': before == after, 'browser': 'NOT RUN'}))
