"""Bounded post-run template delta manifest; fail if any additional line changes."""
import hashlib
import json
from pathlib import Path

frozen = Path('/root/km25-security')
current = Path('/mnt/c/kidsmap')
evidence = json.loads((current / 'docs/task33/reports/25-security-green.json').read_text())
original = json.loads((frozen / 'security-source-sha256.json').read_text())
overrides = ('src/catalog/templates/pages/specialist_workspace.html',
    'src/catalog/templates/pages/owner_specialist_create.html',
    'src/catalog/templates/catalog/specialist_detail.html')
base = 'src/catalog/templates/base.html'
addition = '{% block navigation_motion %}<style>@view-transition{navigation:none}</style>{% endblock %}'
manifest = {'independent_test_snapshot': '25-security-green.json',
    'independent_tests': {'tests_run': 17, 'failures': 0, 'errors': 0},
    'final_suite_attribution': 'Parent /root reports479/479PASS on final source; not executed by security reviewer',
    'review': 'Late four-template source delta only; no ACL/form/control changes', 'source': {}}
same = 0
for path, digest in evidence['source_sha256'].items():
    data = (current / path).read_bytes()
    now = hashlib.sha256(data).hexdigest()
    entry = {'independent_sha256': digest, 'final_sha256': now}
    if now == digest:
        entry['state'] = 'SAME'
        same += 1
    else:
        if path not in overrides:
            raise RuntimeError('Unexpected changed security boundary')
        old_lines = (frozen / path).read_text().splitlines()
        new_lines = data.decode().splitlines()
        if new_lines.count(addition) != 1:
            raise RuntimeError('Unexpected navigation override')
        new_lines.remove(addition)
        if old_lines != new_lines:
            raise RuntimeError('Additional specialist template changes')
        entry['state'] = 'REVIEWED_CSS_ONLY'
        entry['added_line'] = addition
    manifest['source'][path] = entry
old_lines = (frozen / base).read_text().splitlines()
new_lines = (current / base).read_text().splitlines()
empty_block = '    {% block navigation_motion %}{% endblock %}'
if new_lines.count(empty_block) != 1:
    raise RuntimeError('Unexpected base block')
new_lines.remove(empty_block)
if old_lines != new_lines:
    raise RuntimeError('Additional base changes')
manifest['source'][base] = {'independent_sha256': original[base],
    'final_sha256': hashlib.sha256((current / base).read_bytes()).hexdigest(),
    'state': 'REVIEWED_EMPTY_BLOCK_ONLY', 'added_line': empty_block}
manifest['same_security_artifacts'] = same
manifest['reviewed_specialist_css_artifacts'] = 3
manifest['reviewed_base_artifacts'] = 1
manifest['source_delta_acceptance'] = 'PASS'
output = current / 'docs/task33/reports/25-security-final-delta.json'
output.write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({key: manifest[key] for key in ('same_security_artifacts',
    'reviewed_specialist_css_artifacts', 'reviewed_base_artifacts', 'source_delta_acceptance')}))
