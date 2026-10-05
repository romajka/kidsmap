"""Disposable native recovery launcher using unchanged QA04 containment guards."""
import importlib.util
import os
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('completion_recovery_qa04',HERE.parent.parent/'qa04/run.py')
launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(launcher)
clean=launcher.clean_environment
def environment(root):
    env=clean(root)
    env['PYTHONPATH']=str(HERE/'domain_recovery_bridge')+os.pathsep+str(HERE)+os.pathsep+env['PYTHONPATH']
    metadata=Path(os.environ['TASK33_COMPLETION_ARTIFACT_JSON'])
    if (metadata.name!='artifact.json' or metadata.is_symlink() or not metadata.is_file()
        or not metadata.resolve().is_relative_to(Path('/root/task33-evidence/completion-artifact-c2'))):
        raise RuntimeError('Foreign completion artifact denied')
    env['TASK33_R1_ARTIFACT_JSON']=str(metadata)
    return env
launcher.clean_environment=environment
sys.exit(launcher.main())
