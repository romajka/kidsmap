"""Own-stand creation with exact native commands and source preservation snapshot."""
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
CONTAINER = 'kidsmap-placeqa06-plan-20261010'


def run(argv, output=None):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, encoding='utf-8')
    row = {'argv':argv, 'cwd':str(ROOT), 'exit_code':result.returncode}
    if output:
        (HERE / output).write_text(result.stdout+result.stderr, encoding='utf-8')
        row['output_file'] = output
    else:
        row.update(stdout=result.stdout, stderr=result.stderr)
    with (HERE / 'command-ledger.jsonl').open('a', encoding='utf-8') as file:
        file.write(json.dumps(row)+'\n')
    assert result.returncode == 0, (argv, result.returncode)
    return result.stdout.strip()


head = run(['git','rev-parse','HEAD'])
branch = run(['git','branch','--show-current'])
worktree = run(['git','status','--short'])
run(['git','diff','--exit-code','--stat','HEAD','--','src','static','config','locale'])
files = ['src/config/settings.py','Dockerfile','.github/workflows/deploy.yml','scripts/release-server.sh','docs/qa/module-acceptance-prompts.md']
files += [f'locale/{language}/LC_MESSAGES/django.{ext}' for language in ['ru','az','en'] for ext in ['po','mo']]
files += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / 'docs/superpowers/plans').glob('2026-10-10-place-qa0[1-5]-*.md'))]
active = next(x for x in (ROOT/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if x.startswith('active_run:'))
assert active == 'active_run: NONE'
snapshot = {'recorded_at_utc':datetime.now(timezone.utc).isoformat(), 'head':head,'branch':branch,
    'entry_worktree':worktree.splitlines(),'active_run':active,
    'source_before_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},
    'owned_container':CONTAINER,'application_implementation':'NOT AUTHORIZED'}
snapshot['foreign_stands'] = run(['wsl.exe','--exec','docker','ps','--format','{{.Names}} {{.Ports}}']).splitlines()
snapshot['postgres_image_id'] = run(['wsl.exe','--exec','docker','image','inspect','postgres:17-alpine','--format','{{.Id}}'])
snapshot['container_id'] = run(['wsl.exe','--exec','docker','run','--pull=never','--detach','--name',CONTAINER,
    '--publish','127.0.0.1:55442:5432','--env','POSTGRES_DB=placeqa06_plan','--env','POSTGRES_USER=placeqa06_plan',
    '--env','POSTGRES_HOST_AUTH_METHOD=trust','postgres:17-alpine'])
(HERE/'snapshot.json').write_text(json.dumps(snapshot, indent=2)+'\n', encoding='utf-8')
print('Dedicated QA06 PostgreSQL created.', flush=True)
time.sleep(2)
run(['wsl.exe','--exec','docker','exec',CONTAINER,'pg_isready','-U','placeqa06_plan','-d','placeqa06_plan'])
run([sys.executable, str(HERE/'runtime.py'),'prepare'], 'prepare-runtime.txt')
print('Isolated migration and fixtures ready.', flush=True)
