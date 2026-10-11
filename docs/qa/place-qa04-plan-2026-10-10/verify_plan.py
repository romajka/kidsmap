"""Verify this planning artifact and preservation without changing application files."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = ROOT / 'docs/superpowers/plans/2026-10-10-place-qa04-manual-district.md'
snapshot = json.loads((HERE / 'snapshot.json').read_text(encoding='utf-8'))
ledger_path = HERE / 'command-ledger.jsonl'


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
current_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                 for name in snapshot['source_before_sha256']}
preserved = {name: current_hashes[name] == digest
             for name, digest in snapshot['source_before_sha256'].items()}
# An observed concurrent QA-register edit is preserved, not rolled back or
# silently accepted as hash equality. All application/prior-plan inputs must match.
shared_doc = 'docs/qa/module-acceptance-prompts.md'
assert all(ok for name, ok in preserved.items() if name != shared_doc), preserved
drift = [{'path': name, 'baseline_sha256': snapshot['source_before_sha256'][name],
          'current_sha256': current_hashes[name], 'action': 'left untouched by this task'}
         for name, ok in preserved.items() if not ok]
(HERE / 'preservation-drift.json').write_text(json.dumps(drift, indent=2) + '\n', encoding='utf-8')
active = next(x for x in (ROOT / 'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if x.startswith('active_run:'))
assert active == snapshot['active_run'] == 'active_run: NONE'
baseline = (HERE / 'baseline-district.txt').read_text(encoding='utf-8')
existing = (HERE / 'existing-resolver-tests.txt').read_text(encoding='utf-8')
assert re.search(r'tests 9\b', baseline) and re.search(r'pass 4\b', baseline) and re.search(r'fail 5\b', baseline)
assert re.search(r'tests 7\b', existing) and re.search(r'pass 7\b', existing) and re.search(r'fail 0\b', existing)
assert snapshot['baseline_exit_code'] == 1 and snapshot['existing_suite_exit_code'] == 0
links = []
pending_result = HERE / 'plan-verification.json'
for doc in [PLAN, HERE / 'REPORT.md']:
    content = doc.read_text(encoding='utf-8')
    assert not re.search(r'\b(?:TODO|TBD)\b', content)
    assert all(line.rstrip() == line for line in content.splitlines())
    for link in re.findall(r'\]\(([^)]+)\)', content):
        resolved = (doc.parent / link).resolve()
        assert resolved.is_file() or resolved == pending_result, (doc, link)
        links.append({'document': doc.relative_to(ROOT).as_posix(), 'target': link})
result = {'head': snapshot['head'], 'active_run': active, 'application_diff_empty': True,
          'all_input_hashes_equal': all(preserved.values()),
          'application_and_prior_plan_hashes_equal': True, 'observed_document_drift': drift,
          'documents_checked': 2, 'links_checked': len(links),
          'baseline': {'tests': 9, 'passed': 4, 'failures': 5, 'exit_code': 1},
          'existing_suite': {'tests': 7, 'passed': 7, 'failures': 0, 'exit_code': 0},
          'foreign_stands_changed': False, 'browser': 'NOT RUN', 'db_save_reload': 'NOT RUN',
          'approval': 'PENDING', 'links': links}
pending_result.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'links'}))
