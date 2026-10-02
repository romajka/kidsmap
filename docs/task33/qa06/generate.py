#!/usr/bin/env python3
"""Generate additive migration inside the unchanged QA04 disposable harness."""
import importlib.util
import os
from pathlib import Path
import sys
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
QA04 = HERE.parent / 'qa04'
spec = importlib.util.spec_from_file_location('qa04_launcher', QA04 / 'run.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
original_environment = launcher.clean_environment
def environment(root):
    env = original_environment(root)
    env['PYTHONPATH'] = str(HERE) + os.pathsep + env['PYTHONPATH']
    return env
launcher.clean_environment = environment
sys.exit(launcher.main())
