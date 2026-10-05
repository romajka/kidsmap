"""Owned current-source mirror and unchanged disposable QA04 guards."""
import importlib.util
import shutil
import sys
from pathlib import Path
SOURCE=Path('/mnt/c/kidsmap');ROOT=Path('/root/km-completion-domain')
ROOT.mkdir(exist_ok=True)
for name in ('src','static','templates','locale','docs/task33/qa04'):
    shutil.copytree(SOURCE/name,ROOT/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
if not (ROOT/'.venv').exists():(ROOT/'.venv').symlink_to('/root/kidsmap-task33/.venv',target_is_directory=True)
spec=importlib.util.spec_from_file_location('domain_guarded_qa04',ROOT/'docs/task33/qa04/run.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
sys.exit(base.main())
