"""Verify audit deliverables and preserve the recorded failing baseline."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = ROOT / 'docs/superpowers/plans/2026-10-10-place-qa02-map-fallback.md'
snapshot = json.loads((HERE / 'snapshot.json').read_text(encoding='utf-8'))
commands = [
    ['git', 'rev-parse', 'HEAD'],
    ['git', 'status', '--short'],
    ['git', 'diff', '--exit-code', '--stat', 'HEAD', '--', 'src', 'static', 'config', 'locale'],
    ['git', 'diff', '--check'],
]
rows = []
for argv in commands:
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, encoding='utf-8')
    rows.append({'argv': argv, 'cwd': str(ROOT), 'exit_code': result.returncode,
                 'stdout': result.stdout, 'stderr': result.stderr})
with (HERE / 'command-ledger.jsonl').open('a', encoding='utf-8') as ledger:
    for row in rows:
        ledger.write(json.dumps(row, ensure_ascii=False) + '\n')
assert all(row['exit_code'] == 0 for row in rows)
assert rows[0]['stdout'].strip() == snapshot['head']
assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
           for name, digest in snapshot['source_before_sha256'].items())
active = next(x for x in (ROOT / 'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if x.startswith('active_run:'))
assert active == snapshot['active_run'] == 'active_run: NONE'
links = []
for doc in [PLAN, HERE / 'REPORT.md']:
    text = doc.read_text(encoding='utf-8')
    assert not re.search(r'\b(?:TODO|TBD)\b', text)
    assert all(line == line.rstrip() for line in text.splitlines())
    for link in re.findall(r'\]\(([^)]+)\)', text):
        assert (doc.parent / link).is_file(), (str(doc), link)
        links.append({'file': doc.relative_to(ROOT).as_posix(), 'target': link})
result = {'head': snapshot['head'], 'active_run': active,
          'application_diff_empty': True, 'hashed_inputs_preserved': True,
          'documents_checked': 2, 'links_checked': len(links),
          'baseline': {'tests': 5, 'passed': 0, 'failed': 5, 'exit_code': 1},
          'browser': 'NOT RUN', 'db_save_reload': 'NOT RUN',
          'scope_approval': 'PENDING', 'links': links}
(HERE / 'plan-verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'links'}))
