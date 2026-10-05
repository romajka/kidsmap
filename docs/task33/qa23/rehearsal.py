#!/usr/bin/env python3
"""Run QA23 child inside the unchanged disposable QA04 launcher."""
import importlib.util
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('qa04_r1_launcher', HERE.parent / 'qa04' / 'run.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
original_environment = launcher.clean_environment


def environment(root):
    env = original_environment(root)
    env['PYTHONPATH'] = str(HERE / 'bridge') + os.pathsep + env['PYTHONPATH']
    artifact = os.environ.get('TASK33_R1_ARTIFACT_JSON', '')
    if artifact:
        path = Path(artifact)
        if path.name != 'artifact.json' or not path.is_file() or not path.resolve().is_relative_to(Path('/root/task33-artifacts')):
            raise RuntimeError('Unexpected local R1 artifact metadata path')
        env['TASK33_R1_ARTIFACT_JSON'] = str(path)
    return env


launcher.clean_environment = environment
sys.exit(launcher.main())
