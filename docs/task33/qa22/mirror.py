"""Copy current allowlisted source without environment, DB, media or Git."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

source=Path('/mnt/c/kidsmap'); target=Path('/root/kidsmap-task33')
scopes=['src','config','catalog','manage.py','static','templates','locale','docs/task33/qa04']
tracked=subprocess.check_output(['git','ls-files','-z','--',*scopes],cwd=source)
added=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z','--',*scopes],cwd=source)
hashes={}
for raw in sorted(set((tracked+added).split(b'\0'))):
    if not raw:continue
    path=raw.decode();src=source/path;dst=target/path
    if src.is_symlink()or not src.is_file():raise RuntimeError('Unverified source file')
    if not dst.resolve().is_relative_to(target):raise RuntimeError('Unsafe mirror target')
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    hashes[path]=hashlib.sha256(dst.read_bytes()).hexdigest()
manifest=Path(sys.argv[1]);manifest.parent.mkdir(parents=True,exist_ok=True)
manifest.write_text(json.dumps({'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),'source_sha256':hashes},indent=2))
print('Allowlisted source mirrored; snapshot retained outside Git; no env/DB/media/git copied')
