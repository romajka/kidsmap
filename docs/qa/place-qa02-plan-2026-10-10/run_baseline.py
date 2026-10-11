"""Record read-only source/DOM evidence without Django, DB or external services."""
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LEDGER = HERE / 'command-ledger.jsonl'
entries = []


def run(argv, *, env=None, output=None):
    result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8')
    row = {'argv': argv, 'cwd': str(ROOT), 'exit_code': result.returncode}
    if output:
        (HERE / output).write_text(result.stdout + result.stderr, encoding='utf-8')
        row['output_file'] = output
    else:
        row.update(stdout=result.stdout, stderr=result.stderr)
    entries.append(row)
    return result


head = run(['git', 'rev-parse', 'HEAD'])
branch = run(['git', 'branch', '--show-current'])
status = run(['git', 'status', '--short'])
app_diff = run(['git', 'diff', '--exit-code', '--stat', 'HEAD', '--', 'src', 'static', 'config', 'locale'])
active = next(x for x in (ROOT / 'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if x.startswith('active_run:'))
paths = ['static/js/owner_place_map_picker.js', 'static/js/location_resolution.js',
         'src/catalog/templates/pages/includes/permanent_place_map.html',
         'src/catalog/templates/pages/permanent_place_form.html',
         'src/catalog/services/permanent_place_wizard.py',
         'src/catalog/services/location_assignment.py',
         'docs/superpowers/plans/2026-10-10-place-qa01-rejection-feedback.md',
         'docs/qa/module-acceptance-prompts.md']
before = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
qa_env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH', 'PATHEXT', 'COMSPEC'}}
qa_env.update(DJANGO_TESTING='1', KIDSMAP_JSDOM=str(ROOT / '.tmp/phone-dom/node_modules/jsdom'))
node = r'C:\Program Files\nodejs\node.exe'
version = run([node, '--version'], env=qa_env)
probe = run([node, '--test', str(HERE / 'baseline-map-controls.cjs')], env=qa_env, output='baseline-map-controls.txt')
after = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
result = {
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
    'head': head.stdout.strip(), 'branch': branch.stdout.strip(),
    'worktree_status': status.stdout.splitlines(), 'active_run': active,
    'source_before_sha256': before, 'source_after_sha256': after,
    'preserved': before == after, 'application_diff_from_head_empty': app_diff.returncode == 0,
    'node_version': version.stdout.strip(), 'probe_exit_code': probe.returncode,
    'isolation': {'DJANGO_TESTING': True, 'django_loaded': False, 'database_used': False,
                  'external_requests': False, 'synthetic_dom_only': True, 'provider': 'local stub in late-load test'},
    'browser': 'NOT RUN', 'save_reload': 'NOT RUN', 'backend_tests': 'NOT RUN',
}
(HERE / 'snapshot.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
LEDGER.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in entries), encoding='utf-8')
assert before == after
assert app_diff.returncode == 0
assert probe.returncode == 1, 'Expected baseline assertions to fail; inspect evidence before proceeding.'
print(json.dumps({'probe_exit_code': probe.returncode, 'preserved': before == after, 'application_diff_empty': app_diff.returncode == 0, 'browser': 'NOT RUN'}))
