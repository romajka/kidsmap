"""Copy allowlisted current source only; never .env/media/credentials or prior runtime scratch."""
import importlib.util
import shutil
from pathlib import Path

source=Path('/mnt/c/kidsmap'); mirror=Path('/root/km-completion-security')
spec=importlib.util.spec_from_file_location('artifact',source/'docs/task33/qa28/artifact.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
mirror.mkdir(exist_ok=True)
names=set(module.ROOT_FILES)
for scope in module.SCOPES:
    names.update(p.relative_to(source).as_posix() for p in (source/scope).rglob('*') if p.is_file() and module.permitted(p.relative_to(source).as_posix()))
count=0
for name in sorted(names):
    path=source/name
    assert path.is_file() and not path.is_symlink()
    target=mirror/name;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(path,target);count+=1
venv=mirror/'.venv'
if not venv.exists():venv.symlink_to('/root/km28-security/.venv',target_is_directory=True)
assert venv.resolve()==Path('/root/km28-security/.venv').resolve()
print({'source_files':count,'mirror':str(mirror),'external_credentials_copied':False})
