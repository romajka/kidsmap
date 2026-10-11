"""Final audit verification; stop only this recorder's own PostgreSQL container."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = ROOT / 'docs/superpowers/plans/2026-10-10-place-qa03-pricing-rebase.md'
snapshot = json.loads((HERE / 'snapshot.json').read_text(encoding='utf-8'))
ledger_path = HERE / 'command-ledger.jsonl'
ledger = [json.loads(line) for line in ledger_path.read_text(encoding='utf-8').splitlines()]


def run(argv):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, encoding='utf-8')
    with ledger_path.open('a', encoding='utf-8') as out:
        out.write(json.dumps({'argv': argv, 'cwd': str(ROOT), 'exit_code': result.returncode,
                              'stdout': result.stdout, 'stderr': result.stderr}) + '\n')
    assert result.returncode == 0, (argv, result.returncode)
    return result.stdout.strip()


assert run(['git', 'rev-parse', 'HEAD']) == snapshot['head']
run(['git', 'status', '--short'])
run(['git', 'diff', '--exit-code', '--stat', 'HEAD', '--', 'src', 'static', 'config', 'locale'])
run(['git', 'diff', '--check'])
preserved = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
             for name, digest in snapshot['source_before_sha256'].items()}
assert all(preserved.values()), preserved
active = next(x for x in (ROOT / 'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if x.startswith('active_run:'))
assert active == snapshot['active_run'] == 'active_run: NONE'
links = []
for doc in [PLAN, HERE / 'REPORT.md']:
    text = doc.read_text(encoding='utf-8')
    assert not re.search(r'\b(?:TODO|TBD)\b', text)
    assert all(line.rstrip() == line for line in text.splitlines())
    for link in re.findall(r'\]\(([^)]+)\)', text):
        assert (doc.parent / link).is_file(), (doc, link)
        links.append({'document': doc.relative_to(ROOT).as_posix(), 'target': link})
created = next(row for row in ledger if row['argv'][:4] == ['wsl.exe', '--exec', 'docker', 'run'])
container_id = created['stdout'].strip()
assert re.fullmatch('[0-9a-f]{64}', container_id)
assert run(['wsl.exe', '--exec', 'docker', 'inspect', container_id, '--format', '{{.Name}}']) == '/' + snapshot['owned_container']
run(['wsl.exe', '--exec', 'docker', 'stop', container_id])
assert run(['wsl.exe', '--exec', 'docker', 'inspect', container_id, '--format', '{{.State.Running}}']) == 'false'
result = {'head': snapshot['head'], 'active_run': active, 'application_diff_empty': True,
          'hashed_inputs_preserved': True, 'documents_checked': 2, 'links_checked': len(links),
          'baseline': {'tests': 6, 'passed': 3, 'failures': 2, 'errors': 1, 'exit_code': 1},
          'own_container': snapshot['owned_container'], 'own_container_status': 'stopped; not removed',
          'foreign_stands_changed': False, 'browser': 'NOT RUN', 'approval': 'PENDING', 'links': links}
(HERE / 'plan-verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'links'}))
