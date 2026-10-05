"""Hash tested source without copying source, env or fixture records into Git."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
windows = Path('/mnt/c/kidsmap')
linux = Path('/root/kidsmap-task33')
git = lambda *args: subprocess.check_output(['git', '-C', str(windows), *args]).decode().splitlines()
paths = {row['path'] for row in json.loads(Path(sys.argv[2]).read_text())['files']} if len(sys.argv) > 2 else set(git('diff', '--name-only')) | set(git('ls-files', '--others', '--exclude-standard', 'src', 'locale', 'static'))
rows = []
for relative in sorted(paths):
    if not relative.startswith(('src/', 'locale/', 'static/')) or relative.endswith(('.mo', '.pyc')):
        continue
    source = windows / relative
    mirrored = linux / relative
    if not source.is_file():
        continue
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    mirror_digest = hashlib.sha256(mirrored.read_bytes()).hexdigest() if mirrored.is_file() else None
    rows.append(dict(path=relative, sha256=digest, mirror_sha256=mirror_digest, match=digest == mirror_digest))
result = dict(head=git('rev-parse', 'HEAD')[0], branch=git('branch', '--show-current')[0], source='dirty stage21 worktree', files=rows, all_mirrored=all(x['match'] for x in rows))
Path(sys.argv[1]).write_text(json.dumps(result, indent=2))
print(json.dumps(dict(branch=result['branch'], head=result['head'], count=len(rows), all_mirrored=result['all_mirrored'])))
