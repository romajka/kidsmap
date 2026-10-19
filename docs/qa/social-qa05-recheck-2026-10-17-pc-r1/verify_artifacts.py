"""Evidence/source integrity gate for this PLAN snapshot, not product acceptance.

Run from any cwd with Python stdlib. After source changes, retain this report as
history; do not alter assertions to make a later application patch fit this gate.
"""
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import re
import struct
import subprocess
from urllib.request import urlopen

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
QA = ROOT / '.tmp/social05-pc-plan-r1'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
digest = lambda s: hashlib.sha256(s.encode('utf-8')).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8'))


def git(*args):
    return subprocess.check_output(
        ['git', *args], cwd=ROOT, text=True, encoding='utf-8'
    ).rstrip('\r\n')


entry = load(OUT / 'source-entry.json')
assert git('rev-parse', 'HEAD') == entry['head'] == '852938d96764ae315b92859e3651e5ea62054a36'
assert git('branch', '--show-current') == entry['branch'] == 'codex/module09-transfer-2026-10-16-r1'
assert git('rev-parse', 'task33-progress') == entry['task33_ref']
assert git('rev-parse', 'HEAD^{tree}') == entry['index_tree']
assert not git('diff', '--cached', '--name-only')
assert len(entry['sources']) == 1021
assert all(sha(ROOT / p) == h for p, h in entry['sources'].items())
assert load(OUT / 'source-final.json')['sources'] == entry['sources']
assert all(sha(ROOT / p) == h for p, h in entry['shared_mo'].items())
assert sha(ROOT / '.cbmignore') == entry['cbmignore_sha256']
active = [s for s in (ROOT / 'docs/task33/implementation-status.md').read_text(
    encoding='utf-8').splitlines() if s.startswith('active_run:')]
assert active == entry['active_run'] == ['active_run: NONE']
assert not git('diff', '--name-only', '--', 'static/css/site.css')

entry_paths = {s[3:] for s in entry['status'].splitlines() if s}
current_paths = {s[3:] for s in git('status', '--porcelain=v1', '-uall').splitlines() if s}
new_prefix = OUT.relative_to(ROOT).as_posix() + '/'
assert entry_paths <= current_paths
assert all(p in entry_paths or p.startswith(new_prefix) for p in current_paths)

guide = ROOT / 'docs/qa/continuation-and-repair-prompts-2026-10-11.md'
note = (OUT / 'status-note.md').read_bytes().replace(b'\r\n', b'\n').rstrip(b'\n') + b'\n\n'
guide_bytes = guide.read_bytes()
assert guide_bytes.count(note) == 1
assert hashlib.sha256(guide_bytes.replace(note, b'', 1)).hexdigest() == entry['guide_sha256']

old_counts = {}
for name, expected in [
    ('module09-pc-resume-2026-10-16-r1', 43),
    ('social-qa03-fix-2026-10-16-pc-r1', 181),
    ('social-qa04-recheck-2026-10-16-pc-r1', 149),
    ('social-qa04-fix-2026-10-17-pc-r1', 212),
]:
    parent = OUT.parent / name
    manifest = load(parent / 'artifact-manifest.json')
    assert len(manifest) == expected, (name, len(manifest))
    assert all(sha(parent / p) == h for p, h in manifest.items()), name
    old_counts[name] = len(manifest)

candidate = load(OUT / 'candidate-manifest.json')
before = (ROOT / 'static/css/site.css').read_text(encoding='utf-8')
rules = (OUT / 'candidate-rules.css').read_text(encoding='utf-8')
anchor = '/* Public reviews of catalog listings */'
assert before.count(anchor) == 1 and not candidate['applied']
assert digest(before) == candidate['before_normalized_sha256']
assert digest(before.replace(anchor, rules + '\n' + anchor, 1)) == candidate['after_normalized_sha256']
assert sha(OUT / 'candidate-rules.css') == candidate['candidate_rules_sha256']
assert sha(OUT / 'proposed.diff') == candidate['proposed_diff_sha256']
assert 'overflow' not in rules and candidate['application_file'] == 'static/css/site.css'
patchcheck = subprocess.run(
    ['git', 'apply', '--check', '--ignore-space-change', str(OUT / 'proposed.diff')],
    cwd=ROOT, capture_output=True, text=True
)
assert patchcheck.returncode == 0, patchcheck.stderr

matrix = load(OUT / 'matrix.json')
expected_cells = set(itertools.product(
    ['author', 'guest'], ['ru', 'az', 'en'], [360, 390, 768, 1024, 1280, 1440]
))
assert len(matrix) == 36
assert {(r['item']['role'], r['item']['lang'], r['item']['width']) for r in matrix} == expected_cells
assert all(len(r['controls']) == 9 and all(r['controls'].values()) for r in matrix)
assert sum(sum(r['controls'].values()) for r in matrix) == 324
assert sum(sum(r['layout'].values()) for r in matrix) == 210
assert sum(sum(not v for v in r['layout'].values()) for r in matrix) == 24
failed = [r for r in matrix if not all(r['layout'].values())]
assert len(failed) == 3
assert {(r['item']['role'], r['item']['lang'], r['item']['width']) for r in failed} == {
    ('author', lang, 768) for lang in ['ru', 'az', 'en']
}
assert all(r['facts']['documentWidth'] == 822 and not any(r['layout'].values()) for r in failed)
assert all(len(r['layout']) == (8 if r['item']['role'] == 'author' else 5) for r in matrix)
assert all(r['before'] == r['after'] for r in matrix)
assert all(not r[k] for r in matrix for k in ['pageerrors', 'http_failures', 'request_failed'])

probe = load(OUT / 'probe.json')
assert len(probe) == 7 and sum(sum(r['checks'].values()) for r in probe) == 49
assert all(len(r['checks']) == 7 and all(r['checks'].values()) for r in probe)
assert {(r['lang'], r['width']) for r in probe} == {
    ('ru', 768), ('az', 768), ('en', 768), ('ru', 360), ('ru', 760), ('ru', 761), ('ru', 1024)
}
for r in probe:
    assert r['before'] == r['restored'] and r['stateBefore'] == r['stateAfter']
    assert r['preview']['documentWidth'] <= r['width'] + 1
    assert r['attribution'].startswith('SIMULATED')
    assert all(r['before'][k] == r['preview'][k] for k in [
        'rootOverflow', 'bodyOverflow', 'panelOverflow'
    ])
    if r['width'] == 768:
        assert r['before']['documentWidth'] == 822 and r['preview']['documentWidth'] == 768
attempt = load(OUT / 'probe-attempt1.json')
assert len(attempt) == 7
assert sum(sum(not v for v in r['checks'].values()) for r in attempt) == 1
assert attempt[-1]['lang'] == 'ru' and attempt[-1]['width'] == 1024
assert not attempt[-1]['checks']['restored_original_geometry']
assert all(all(r['checks'].values()) for r in attempt[:-1])
assert [r['before'] for r in probe[:-1]] == [r['before'] for r in attempt[:-1]]
assert probe[-1]['png'].endswith('-stable.png')

pngs = load(OUT / 'png-manifest.json')
assert len(pngs) == 44
assert Counter(r['kind'] for r in pngs) == {
    'baseline': 36, 'simulated-preview': 7, 'retained-preview-attempt': 1
}
assert len({r['path'] for r in pngs}) == 44
assert {p.relative_to(OUT).as_posix() for p in (OUT / 'screenshots').glob('*.png')} == {
    r['path'] for r in pngs
}
for r in pngs:
    p = OUT / r['path']
    raw = p.read_bytes()
    assert sha(p) == r['sha256'] and raw[:8] == b'\x89PNG\r\n\x1a\n' and r['native']
    assert struct.unpack('>II', raw[16:24]) == (r['width'], r['height'])
assert all((OUT / r['png']).is_file() for r in matrix + probe)

log = (OUT / 'baseline.log').read_text(encoding='utf-8')
assert (OUT / 'baseline.exit').read_text().strip() == '0'
assert 'Ran 3 tests in 0.381s' in log and '\nOK\n' in log
method_ids = re.findall(r'\((catalog\.testcases\.public\.TestReviewEnhancements\.[^)]+)\) \.\.\.', log)
assert len(method_ids) == len(set(method_ids)) == 3
assert not re.search(r'^FAIL:|^ERROR:', log, re.M)

runtime = load(OUT / 'runtime-info.json')
assert runtime['info'] == load(OUT / 'live-final.json')
assert runtime['info']['testing'] and runtime['info']['source_files'] == 1021
assert all(entry['sources'][p] == h for p, h in runtime['info']['hashes'].items())
assert runtime['info']['sole_locales'] == ['/mnt/c/kidsmap/.tmp/social05-pc-plan-r1/locales/locale']
locales = load(OUT / 'locale-manifest.json')
assert locales['status'] == 'complete' and set(locales['locales']) == {'ru', 'az', 'en'}
for r in locales['entries']:
    assert sha(ROOT / 'locale' / r['source']) == r['po_sha256']
    assert sha(QA / 'locales' / r['snapshot']) == r['po_sha256']
    assert sha(QA / 'locales' / r['mo']) == r['mo_sha256']
    assert r['exit_code'] == 0

containers = subprocess.check_output([
    'wsl', '-d', 'Ubuntu-24.04', '--', 'docker', 'ps', '-a', '--format',
    '{{.ID}} {{.Names}} {{.State}} {{.Ports}}'
], text=True)
byname = lambda s: {l.split()[1]: l.split()[:3] for l in s.splitlines() if l.strip()}
old, current = byname((OUT / 'containers-entry.txt').read_text()), byname(containers)
assert len(old) == 32 and all(current.get(k) == v for k, v in old.items())
assert current['m09s05-plan-r1-app'][2] == current['m09s05-plan-r1-pg'][2] == 'running'
with urlopen('http://127.0.0.1:33325/qa/info/', timeout=10) as response:
    live = json.loads(response.read())
assert live == runtime['info']

required = ['REPORT.md', 'IMPLEMENTATION_PLAN.md', 'commands.md', 'next-prompt.txt', 'status-note.md']
for name in required:
    path = OUT / name
    text = path.read_text(encoding='utf-8')
    assert not any(line.endswith((' ', '\t')) for line in text.splitlines()), name
    for link in re.findall(r'\]\(([^)]+)\)', text):
        if '://' in link or link.startswith('#'):
            continue
        relative = link.split('#')[0]
        base = guide.parent if name == 'status-note.md' else OUT
        assert (base / relative).exists() or relative == 'artifact-manifest.json', (name, link)
for p in OUT.glob('*.py'):
    ast.parse(p.read_text(encoding='utf-8'), filename=p.name)
assert not any(p.name in {'.env', 'qa_settings.py', 'runtime.py'} for p in OUT.rglob('*'))

# Only after all assertions: save final read-only observations and artifact gate.
(OUT / 'containers-final.txt').write_text(containers, encoding='utf-8')
preservation = load(OUT / 'preservation.json')
assert preservation['source1021_match_entry'] and preservation['application_changes_this_run'] == 0
assert preservation['foreign_restart_commands'] == 0 and preservation['entry_containers'] == 32
data = load(OUT / 'verification.json')
assert data['application_changes_this_run'] == 0 and not data['proposal']['applied']
assert len(data['qa_attempts']) == 4
assert data['guide_update']['after_sha256'] == sha(guide)
manifest = {
    p.relative_to(OUT).as_posix(): sha(p)
    for p in sorted(OUT.rglob('*')) if p.is_file()
    and p.name not in {'verification.json', 'artifact-manifest.json'}
}
(OUT / 'artifact-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
assert all(sha(OUT / p) == h for p, h in load(OUT / 'artifact-manifest.json').items())
data['metadata_gate'] = 'PASS: evidence/source integrity only; SOCIAL05 remains OPEN, implementation approval PENDING'
data['final_utc'] = datetime.now(timezone.utc).isoformat()
data['artifact_manifest'] = {'files': len(manifest), 'sha256': sha(OUT / 'artifact-manifest.json'),
                             'excludes': ['artifact-manifest.json', 'verification.json']}
data['old_artifact_manifests_verified'] = old_counts
data['backend_method_ids'] = method_ids
data['final_verifier_exit'] = 0
(OUT / 'verification.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({
    'integrity_gate': 'PASS', 'application_changes': 0, 'source_files': 1021,
    'matrix': '36 cells /324controls /210layoutPASS /24layoutFAIL',
    'backend': '3 unique PASS', 'SIMULATED': '7 accepted /49PASS; original failed attempt retained',
    'PNG': 44, 'foreign_containers_preserved': 32, 'artifacts': len(manifest),
    'decision': data['decision'], 'utc': data['final_utc']
}, ensure_ascii=False))
