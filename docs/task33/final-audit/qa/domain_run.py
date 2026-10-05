"""AUDIT-only own mirror and unchanged guarded QA04 launcher."""
import importlib.util
import json
from pathlib import Path
import sys
import tarfile

SOURCE=Path('/mnt/c/kidsmap')
ROOT=Path('/root/km-final-domain')
META=Path('/root/task33-evidence/stage28-artifact-20261003/r2-local-sha256-65d8995ff21fb5e5b9fb88d81d18f2f36c4380841f14131cd11dc258bf8c61b2/artifact.json')
if not ROOT.exists():
    artifact=json.loads(META.read_text());ROOT.mkdir()
    with tarfile.open(artifact['archive']) as archive:
        for member in archive.getmembers():
            target=ROOT/member.name
            assert target.resolve().is_relative_to(ROOT) and not member.issym() and not member.islnk()
        archive.extractall(ROOT,filter='data')
    (ROOT/'.venv').symlink_to('/root/kidsmap-task33/.venv',target_is_directory=True)
HERE=SOURCE/'docs/task33/final-audit/qa'
spec=importlib.util.spec_from_file_location('domain_qa04',ROOT/'docs/task33/qa04/run.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
clean=base.clean_environment
def environment(run_root):
    env=clean(run_root)
    env['PYTHONPATH']=str(HERE/'domain_bridge')+':'+str(HERE)+':'+env['PYTHONPATH']
    return env
base.clean_environment=environment
sys.exit(base.main())
