import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
items = []
for name, reason in [('matrix.result.json', 'Interrupted first matrix: stale transformed drawer-close QA automation; no exported assertions.'), ('batch.result.json', 'Python batch file was mistakenly sent to the JavaScript CLI; SyntaxError, no application execution.')]:
    path = HERE / name
    raw = path.read_text(encoding='utf-8')
    archive = HERE / (path.stem + '.raw-harness-error.txt')
    archive.write_text(raw, encoding='utf-8')
    path.write_text(json.dumps({'qa_harness_error': True, 'not_application_evidence': True, 'reason': reason, 'cli_exit': 1, 'rows': [], 'raw_archive': archive.name, 'raw_sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest()}, indent=2), encoding='utf-8')
    items.append({'file': name, 'raw_archive': archive.name, 'reason': reason})
invalid = HERE / 'batch.effective.js'
archive = HERE / 'batch.invalid-python-attempt.txt'
assert invalid.resolve().parent == HERE.resolve() and archive.resolve().parent == HERE.resolve()
invalid.rename(archive)
items.append({'renamed_from': invalid.name, 'retained_as': archive.name, 'reason': 'Preserve wrongly dispatched Python source as text, not executable JS.'})
(HERE / 'harness-error-inventory.json').write_text(json.dumps(items, indent=2), encoding='utf-8')
verification = HERE / 'verification.json'
if verification.exists():
    prior = HERE / 'verification.attempt1.json'
    assert prior.resolve().parent == HERE.resolve()
    prior.write_bytes(verification.read_bytes())
print(json.dumps({'preserved_harness_errors': len(items), 'ownership_assertion': True}))
