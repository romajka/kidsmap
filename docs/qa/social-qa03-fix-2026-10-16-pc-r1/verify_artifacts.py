"""Check this approved local repair and evidence; never executes application tests.

Reads Git/source, owned scratch locale assets and evidence. Writes only this QA
package's manifest/verification metadata. Historical failed attempts stay failed.
Run from the original C:/kidsmap checkout while this scoped WORKTREE is current.
"""
import ast
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
QA = ROOT / '.tmp/social03-pc-fix-r1'
PRIOR = ROOT / 'docs/qa/module09-pc-resume-2026-10-16-r1'
CANDIDATES = ROOT / 'docs/qa/social-qa03-recheck-2026-10-16-r1/candidate'
GUIDE = ROOT / 'docs/qa/continuation-and-repair-prompts-2026-10-11.md'
MODIFIED = {
    'src/catalog/controllers/typed_reviews.py',
    'src/catalog/templates/catalog/typed_reviews.html',
}
NEW_TEST = 'src/catalog/testcases/test_social_qa03_conflict_recovery.py'
APPROVED = MODIFIED | {NEW_TEST}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def git(*args):
    result = subprocess.run(['git', '-c', 'core.quotepath=false', *args], cwd=ROOT,
                            capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0, (args, result.returncode, result.stderr)
    return result.stdout.rstrip('\r\n')


def all_true(rows):
    assert all(all(value is True for value in row['checks'].values()) for row in rows)


entry, green, red = map(read, ['entry.json', 'green-source.json', 'red-source.json'])
approval, data = read('approval.json'), read('verification.json')
assert set(approval['application_files']) == APPROVED
assert sha(PRIOR / 'IMPLEMENTATION_PLAN.md') == approval['plan_sha256']
assert git('rev-parse', 'HEAD') == entry['head'] == data['snapshot']['head']
assert git('branch', '--show-current') == entry['branch']
assert git('rev-parse', 'task33-progress') == entry['initial_task33_ref']
assert git('rev-parse', 'HEAD^{tree}') == entry['index_tree']
git('diff', '--cached', '--exit-code')
git('diff', '--check')
source_roots = ['src', 'static', 'templates', 'scripts', 'config', 'locale']
assert set(git('diff', '--name-only', '--', *source_roots).splitlines()) == MODIFIED
assert len(entry['sources']) == 1019 and len(green['sources']) == 1020
assert set(green['sources']) == set(entry['sources']) | {NEW_TEST}
assert all(sha(ROOT / path) == digest for path, digest in green['sources'].items())
assert all(sha(ROOT / path) == digest for path, digest in entry['sources'].items()
           if path not in MODIFIED)
assert all(red['sources'][path] == digest for path, digest in entry['sources'].items())
assert red['sources'][NEW_TEST] == green['sources'][NEW_TEST]
assert all(sha(ROOT / path) == digest for path, digest in entry['shared_mo'].items())
active = [line for line in (ROOT / 'docs/task33/implementation-status.md')
          .read_text(encoding='utf-8').splitlines() if line.startswith('active_run:')]
assert active == entry['active_run'] == ['active_run: NONE']
for path in APPROVED:
    assert (ROOT / path).read_text(encoding='utf-8') == (
        CANDIDATES / Path(path).name).read_text(encoding='utf-8')
    assert sha(ROOT / path) == read('patch-scope.json')[path]['sha256']
    assert read('patch-scope.json')[path]['normalized_matches_approved_candidate'] is True

late = read('late-observed-local-state.json')
assert sha(ROOT / '.cbmignore') == late['.cbmignore']['sha256']
allowed_docs = ('docs/qa/module09-pc-resume-2026-10-16-r1/',
                'docs/qa/social-qa03-fix-2026-10-16-pc-r1/')
for line in git('status', '--porcelain=v1', '-uall').splitlines():
    path = line[3:]
    assert (path in APPROVED or path == GUIDE.relative_to(ROOT).as_posix()
            or path == '.cbmignore' or path.startswith(allowed_docs)), line
prior_manifest = json.loads((PRIOR / 'artifact-manifest.json').read_text(encoding='utf-8'))
assert all(sha(PRIOR / path) == digest for path, digest in prior_manifest.items())
note = (OUT / 'status-note.md').read_bytes().rstrip(b'\r\n') + b'\n\n'
assert GUIDE.read_bytes().count(note) == 1
assert hashlib.sha256(GUIDE.read_bytes().replace(note, b'', 1)).hexdigest() == entry['guide_sha256']

matrix, race, guards, retry = map(read, ['matrix.json', 'race.json', 'guards.json', 'retry.json'])
kinds = ('place', 'activity', 'specialist', 'event')
langs = ('ru', 'az', 'en')
for name, rows, widths, count, observations in [
    ('matrix', matrix, (360, 390, 768, 1024, 1280, 1440), 72, 1224),
    ('race', race, (390, 1440), 24, 314),
    ('guards', guards, (390, 1440), 24, 264),
    ('retry', retry, (390, 1440), 24, 222),
]:
    expected = {(kind, lang, width) for kind in kinds for lang in langs for width in widths}
    assert len(rows) == count
    assert {(r['item']['kind'], r['item']['lang'], r['item']['width']) for r in rows} == expected
    all_true(rows)
    assert sum(len(r['checks']) for r in rows) == observations
    assert data['native_counts'][name] == {'cases': count, 'pass': observations, 'fail': 0}
assert all(r['status'] == 409 and len(r['checks']) == 17 for r in matrix)
assert sum(len(r['pageerrors']) for rows in [matrix, read('raceprep.json'), race, guards, retry]
           for r in rows) == data['normal_unhandled_pageerrors'] == 0
assert 'HTTP409' in race[0]['check_evidence']['draft_script_long_retained']
supplement = read('normalization-supplement.json')
assert supplement['status'] == 409 and supplement['raw_length'] == 1289
assert supplement['validated_length'] == supplement['returned_length'] == 1288
all_true([supplement])
assert len(retry[0]['checks']) == 7 and 'no second B POST' in retry[0]['attribution']
assert sum(bool(r.get('loading')) for r in retry) == 4
extra = read('extra.json')
assert len(extra['transport']) == 4
all_true(extra['transport'])
all_true([extra['accessibility']])
assert all(r['simulated'] and r['events'] for r in extra['transport'])
attempts = read('failed-attempts.json')
assert len(attempts) >= 8 and any(a['id'] == 'QA-LOADING-GATE' for a in attempts)
assert any(value is False for row in read('race-attempt1.json') for value in row['checks'].values())
assert 'FALSE' in (OUT / 'REPORT.md').read_text(encoding='utf-8')

red_log, green_log = [(OUT / name).read_text(encoding='utf-8') for name in ['red.log', 'green.log']]
assert int((OUT / 'red.exit').read_text()) == 1
assert 'Ran 6 tests in 8.811s' in red_log and 'FAILED (failures=14)' in red_log
assert len(set(re.findall(r'^FAIL: (test_\w+)', red_log, re.M))) == 3
assert int((OUT / 'green.exit').read_text()) == 0
assert 'Ran 10 tests in 9.808s' in green_log and '\nOK\n' in green_log
assert len(set(re.findall(r'^(test_\w+) \(', green_log, re.M))) == 10

pngs = read('png-manifest.json')
assert len(pngs) == 127 and len({p['path'] for p in pngs}) == 127
assert {p['path'] for p in pngs} == {
    p.relative_to(OUT).as_posix() for p in (OUT / 'screenshots').glob('*.png')}
assert sum(p['kind'] == 'accepted-ui' for p in pngs) == 121
assert sum(p['kind'] == 'simulated' for p in pngs) == 4
assert sum(p['kind'] == 'retained-attempt' for p in pngs) == 2
for item in pngs:
    path = OUT / item['path']
    raw = path.read_bytes()
    assert sha(path) == item['sha256'] and raw[:8] == b'\x89PNG\r\n\x1a\n'
    assert struct.unpack('>II', raw[16:24]) == (item['width'], item['height'])
    assert item['native'] is True
for rows in [matrix, race, retry, extra['transport'], [extra['accessibility']]]:
    assert all((OUT / row['png']).exists() for row in rows)

live = read('live-final.json')
assert live['testing'] and live['phase'] == 'green' and live['cooldown'] == 120
assert live['controller_sha256'] == green['sources']['src/catalog/controllers/typed_reviews.py']
assert live['template_sha256'] == green['sources']['src/catalog/templates/catalog/typed_reviews.html']
manifest = read('locale-manifest.json')
assert live['sole_locales'] == [manifest['locale_root']]
assert set(manifest['locales']) == set(langs) and len(manifest['entries']) == 3
for item in manifest['entries']:
    assert sha(ROOT / 'locale' / item['source']) == item['po_sha256']
    assert sha(QA / 'locales' / item['snapshot']) == item['po_sha256']
    assert sha(QA / 'locales' / item['mo']) == item['mo_sha256']
style = read('style-observation.json')
assert style['css_unchanged'] and 2.77 < style['contrast'] < 2.79
assert style['normal'] == style['conflict']

links = 0
for path in OUT.glob('*.md'):
    text = path.read_text(encoding='utf-8')
    assert not re.search(r'[ \t]+$', text, re.M), path
    base = GUIDE.parent if path.name == 'status-note.md' else path.parent
    for target in re.findall(r'\[[^]\n]+\]\(([^)\n]+)\)', text):
        if target.startswith(('http://', 'https://', '#')):
            continue
        assert (base / target.split('#', 1)[0]).exists(), (path, target)
        links += 1
for path in OUT.glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
assert not any((OUT / name).exists() for name in ['qa_settings.py', 'runtime.py', 'storage-state.json', '.env'])
artifacts = {p.relative_to(OUT).as_posix(): sha(p) for p in sorted(OUT.rglob('*'))
             if p.is_file() and p.name not in {'verification.json', 'artifact-manifest.json'}}
(OUT / 'artifact-manifest.json').write_text(json.dumps(artifacts, indent=2) + '\n', encoding='utf-8')
data['metadata_gate'] = 'VERIFIED scoped source/evidence integrity; functional closure03 only; module09 OPEN'
data['metadata_integrity'] = {
    'source1020_match_green': True, 'unapproved_entry_source_match': True,
    'approved_candidate_matches': 3, 'existing_test_assertions_changed': False,
    'head_branch_task33_index_active_run_match': True, 'shared_mo_match': True,
    'prior_package_manifest_match_files': len(prior_manifest),
    'guide_original_bytes_preserved': True, 'untracked_cbmignore_retained_since_late_observation': True,
    'png_sha_dimensions_verified': 127, 'document_links_verified': links,
    'git_diff_check_exit': 0, 'artifact_manifest_files': len(artifacts),
    'live_final_source_locales_match': True,
    'failed_attempts_preserved_without_pass_relabeling': True,
}
(OUT / 'verification.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(data['metadata_integrity']))
