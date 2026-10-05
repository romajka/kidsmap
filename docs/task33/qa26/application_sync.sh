#!/bin/bash
set -euo pipefail
mirror=/root/km26-browser-frozen
mkdir -p "$mirror"
for name in src templates static locale docs/task33/qa04 docs/task33/qa26 config scripts; do
 mkdir -p "$mirror/$(dirname "$name")"
 rsync -a --exclude=__pycache__ --exclude='*.pyc' "/mnt/c/kidsmap/$name" "$mirror/$(dirname "$name")/"
done
test -e "$mirror/.venv" || ln -s /root/km24-security/.venv "$mirror/.venv"
cp /mnt/c/kidsmap/manage.py "$mirror/"
find "$mirror/locale" -name django.po -print0 | while IFS= read -r -d '' po; do msgfmt "$po" -o "${po%.po}.mo"; done
"$mirror/.venv/bin/python" - "$mirror" <<'PY'
import ast,hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]); hashes={}
for domain in ['src','templates','static','locale','docs/task33/qa04','docs/task33/qa26','config','scripts']:
 for p in sorted((root/domain).rglob('*')):
  if p.is_file() and p.suffix!='.pyc':
   hashes[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in (root/'docs/task33/qa26').rglob('application*.py'):ast.parse(p.read_text())
for p in (root/'docs/task33/qa26/application_bridge').glob('*.py'):ast.parse(p.read_text())
(root/'browser-source-sha256.json').write_text(json.dumps(hashes,indent=2))
print('Frozen allowlisted mirror and harness AST PASS')
PY
