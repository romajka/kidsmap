"""Run unchanged legacy assertion with diagnostic-only admin payload replay."""
import importlib.util
import os
from pathlib import Path
import sys
import shutil
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
path=Path('/root/kidsmap-task33/docs/task33/qa04/run.py')
spec=importlib.util.spec_from_file_location('qa04_contract_launcher',path)
launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(launcher)
original=launcher.clean_environment
def environment(root):
    env=original(root)
    env['PYTHONPATH']=str(HERE/'contract_bridge')+os.pathsep+env['PYTHONPATH']
    return env
launcher.clean_environment=environment
result=launcher.main()
output=Path(sys.argv[sys.argv.index('--output')+1])
if output.is_dir():
    assert output.parent==Path('/tmp') and output.name.startswith('task33-stage28-legacy-draft-')
    shutil.copytree(output,Path('/root/task33-evidence')/output.name.removeprefix('task33-'))
sys.exit(result)
