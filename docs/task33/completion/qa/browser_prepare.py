"""Copy immutable audit harness into the authorized completion namespace only."""
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OLD = ROOT / 'docs/task33/final-audit/qa'
for path in OLD.glob('browser*'):
    destination = HERE / path.name
    if destination.exists():
        continue  # preserve new completion edits on repeated preparation
    if path.is_dir():
        shutil.copytree(path, destination, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    else:
        destination.write_bytes(path.read_bytes())
for path in HERE.rglob('*'):
    if (not path.is_file() or not path.relative_to(HERE).parts[0].startswith('browser')
        or path.suffix not in ('.py', '.sh', '.js') or path.name == 'browser_prepare.py'):
        continue
    text = path.read_text(encoding='utf-8')
    text = text.replace('docs/task33/final-audit', 'docs/task33/completion')
    text = text.replace('/root/km28-browser', '/root/km-completion-browser')
    text = text.replace('task33-browser28-', 'task33-completion-browser-')
    text = text.replace('browser28-', 'completion-browser-')
    text = text.replace('acceptance28', 'completion-browser')
    path.write_text(text, encoding='utf-8')
print('Prepared completion-owned harness; immutable final-audit untouched. Do not execute before source freeze.')
