"""Own-resource launcher and command ledger; preserves all existing QA stands."""
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CONTAINER = 'kidsmap-placeqa03-plan-20261010'
ledger = []


def run(argv, output=None, env=None):
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
files = ['src/catalog/services/publication.py', 'src/catalog/services/pricing_plans.py',
         'src/catalog/services/volunteer_places.py', 'src/catalog/models/pricing_plan.py',
         'src/catalog/domain_admin/volunteer.py', 'src/catalog/testcases/test_task33_publication.py',
         'docs/qa/module-acceptance-prompts.md',
         'docs/superpowers/plans/2026-10-10-place-qa01-rejection-feedback.md',
         'docs/superpowers/plans/2026-10-10-place-qa02-map-fallback.md']
before = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}
active = next(x for x in (ROOT / 'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if x.startswith('active_run:'))
assert active == 'active_run: NONE'
image = run(['wsl.exe', '--exec', 'docker', 'image', 'inspect', 'postgres:17-alpine', '--format', '{{.Id}}'])
assert image.returncode == 0
created = run(['wsl.exe', '--exec', 'docker', 'run', '--pull=never', '--detach', '--name', CONTAINER,
    '--publish', '127.0.0.1:55437:5432', '--env', 'POSTGRES_DB=placeqa03_plan',
    '--env', 'POSTGRES_USER=placeqa03_plan', '--env', 'POSTGRES_HOST_AUTH_METHOD=trust', 'postgres:17-alpine'])
assert created.returncode == 0, 'Could not create dedicated QA container; existing resources are untouched.'
print('Dedicated PostgreSQL container created; preparing isolated tests.', flush=True)
ready = False
for attempt in range(12):
    result = run(['wsl.exe', '--exec', 'docker', 'exec', CONTAINER, 'pg_isready', '-U', 'placeqa03_plan', '-d', 'placeqa03_plan'])
    if result.returncode == 0:
        ready = True
        break
    time.sleep(1)
assert ready
qa_env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH', 'PATHEXT', 'COMSPEC'}}
qa_env.update(PYTHONIOENCODING='utf-8', PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
result = run([sys.executable, str(HERE / 'run_tests.py'), 'audit_projection_tests.MixedProjectionTests'], output='baseline-tests.txt', env=qa_env)
after = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}
snapshot = {'recorded_at_utc': datetime.now(timezone.utc).isoformat(), 'head': head,
    'branch': branch, 'entry_worktree': status, 'active_run': active,
    'source_before_sha256': before, 'source_after_sha256': after, 'preserved': before == after,
    'postgres_image_id': image.stdout.strip(), 'owned_container': CONTAINER,
    'test_exit_code': result.returncode, 'browser': 'NOT RUN', 'implementation': 'NOT AUTHORIZED'}
(HERE / 'snapshot.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'test_exit_code': result.returncode, 'preserved': before == after, 'browser': 'NOT RUN'}), flush=True)
assert before == after
