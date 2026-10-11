"""Verify planning evidence and stop only the container created by this audit."""
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = ROOT / 'docs/superpowers/plans/2026-10-10-place-qa06-isolated-locales.md'
snapshot = json.loads((HERE / 'snapshot.json').read_text(encoding='utf-8'))
os.environ['DJANGO_TESTING'] = '1'


def run(argv, expected=0, output=None):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, encoding='utf-8')
    row = {'argv': argv, 'cwd': str(ROOT), 'exit_code': result.returncode,
           'expected_exit_code': expected}
    if output:
        (HERE / output).write_text(result.stdout + result.stderr, encoding='utf-8')
        row['output_file'] = output
    else:
        row.update(stdout=result.stdout, stderr=result.stderr)
    with (HERE / 'command-ledger.jsonl').open('a', encoding='utf-8') as file:
        file.write(json.dumps(row) + '\n')
    assert result.returncode == expected, (argv, result.returncode)
    return result.stdout.strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


run([sys.executable, str(HERE / 'inspect_catalogs.py')], expected=1,
    output='catalog-assertions.txt')
run([sys.executable, str(HERE / 'collect_browser_results.py')], expected=1,
    output='browser-assertions.txt')
catalog = json.loads((HERE / 'catalog-comparison.json').read_text(encoding='utf-8'))
browser = json.loads((HERE / 'browser-assertions.json').read_text(encoding='utf-8'))
assert (catalog['checks'], catalog['matches'], catalog['mismatches']) == (15, 5, 10)
assert (browser['total'], browser['passed'], browser['failed']) == (30, 10, 20)
assert browser['environment_valid'] and not catalog['compiled_assets_written']
compiler_version = run(['wsl.exe', '--exec', 'msgfmt', '--version']).splitlines()[0]
run(['git', 'check-ignore', '-v', *[
    f'locale/{lang}/LC_MESSAGES/django.mo' for lang in ('ru', 'az', 'en')]])
assert run(['git', 'rev-parse', 'HEAD']) == snapshot['head']
run(['git', 'status', '--short'])
run(['git', 'diff', '--exit-code', '--stat', 'HEAD', '--',
     'src', 'static', 'config', 'locale', 'Dockerfile', '.github/workflows', 'scripts'])
run(['git', 'diff', '--check'])
current = {path: digest(ROOT / path) for path in snapshot['source_before_sha256']}
changed = [path for path, value in current.items()
           if value != snapshot['source_before_sha256'][path]]
assert not [path for path in changed if path != 'docs/qa/module-acceptance-prompts.md'], changed
frozen = json.loads((HERE / 'frozen-catalog-manifest.json').read_text(encoding='utf-8'))
assert len(frozen) == 6
for row in frozen:
    assert digest(ROOT / row['source']) == digest(ROOT / row['copy']) == row['sha256']
active = next(line for line in
              (ROOT / 'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines()
              if line.startswith('active_run:'))
assert active == snapshot['active_run'] == 'active_run: NONE'

images = []
for file in sorted((HERE / 'screenshots').glob('*.png')):
    data = file.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n' and data[12:16] == b'IHDR'
    classification = ('visible map viewport' if file.name.endswith('-map-visible.png') else
                      'map element; possible sticky overlap' if file.name.endswith('-map.png') else
                      'description tab')
    images.append({'file': file.relative_to(HERE).as_posix(),
                   'width': int.from_bytes(data[16:20], 'big'),
                   'height': int.from_bytes(data[20:24], 'big'),
                   'sha256': digest(file), 'classification': classification})
assert len(images) == 27
assert sum(row['classification'] == 'visible map viewport' for row in images) == 3
(HERE / 'screenshots-manifest.json').write_text(json.dumps(images, indent=2) + '\n', encoding='utf-8')

container_id = snapshot['container_id']
assert re.fullmatch('[0-9a-f]{64}', container_id)
assert run(['wsl.exe', '--exec', 'docker', 'inspect', container_id, '--format', '{{.Name}}']) == '/' + snapshot['owned_container']
running = run(['wsl.exe', '--exec', 'docker', 'inspect', container_id, '--format', '{{.State.Running}}'])
if running == 'true':
    run(['wsl.exe', '--exec', 'docker', 'stop', container_id])
assert run(['wsl.exe', '--exec', 'docker', 'inspect', container_id, '--format', '{{.State.Running}}']) == 'false'
foreign_now = [line.strip() for line in run([
    'wsl.exe', '--exec', 'docker', 'ps', '--format', '{{.Names}} {{.Ports}}']).splitlines()]
foreign_before = [line.strip() for line in snapshot['foreign_stands']]
with socket.socket() as server:
    server.settimeout(1)
    assert server.connect_ex(('127.0.0.1', 8821)) != 0
browser_ledger = [json.loads(line) for line in
                  (HERE / 'browser-command-ledger.jsonl').read_text(encoding='utf-8').splitlines()]
assert any(row['argv'][-1:] == ['close'] and row['exit_code'] == 0 and 'closed' in row['stdout']
           for row in browser_ledger)
links = []
for doc in (PLAN, HERE / 'REPORT.md'):
    content = doc.read_text(encoding='utf-8')
    assert not re.search(r'\b(?:TODO|TBD)\b', content)
    assert all(line.rstrip() == line for line in content.splitlines())
    for link in re.findall(r'\]\(([^)]+)\)', content):
        path = (doc.parent / link).resolve()
        assert path.is_file() or path == HERE / 'plan-verification.json', (doc, link)
        links.append({'document': doc.relative_to(ROOT).as_posix(), 'target': link})

result = {
    'head': snapshot['head'], 'active_run': active,
    'application_and_build_source_diff_empty': True,
    'shared_po_mo_and_prior_plans_preserved': True,
    'frozen_baseline_copies_identical': True, 'compilation_performed': False,
    'all_input_hashes_equal': not changed, 'observed_document_drift': changed,
    'available_compiler': compiler_version,
    'catalog_assertions': {'checks': 15, 'passed': 5, 'failed': 10, 'exit_code': 1},
    'browser_assertions': {'checks': 30, 'passed': 10, 'failed': 20, 'exit_code': 1,
                           'environment_valid': True},
    'browser': 'Chromium headless shell 153.0.8010.12',
    'screenshots': len(images), 'browser_reload': 'DONE; RU passes, AZ/EN baseline fails',
    'form_save_reload': 'NOT RUN', 'browser_session': 'closed',
    'owned_server': 'stopped; loopback 8821 no longer listening',
    'owned_container': snapshot['owned_container'],
    'owned_container_status': 'stopped; not removed',
    'foreign_stands_snapshot_equal': sorted(foreign_now) == sorted(foreign_before),
    'initial_foreign_stands_still_running': set(foreign_before).issubset(foreign_now),
    'new_foreign_stands_observed': sorted(set(foreign_now) - set(foreign_before)),
    'missing_initial_foreign_stands_observed': sorted(set(foreign_before) - set(foreign_now)),
    'implementation': 'NOT AUTHORIZED', 'approval': 'PENDING',
    'documents_checked': 2, 'links_checked': len(links), 'links': links,
}
(HERE / 'plan-verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'links'}))
