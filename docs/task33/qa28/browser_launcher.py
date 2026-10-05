"""Stage28 browser-only bridge using unmodified disposable QA04 launcher."""
import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
family = os.environ.get('TASK33_BROWSER_FAMILY')
if family not in ('r1', 'specialist', 'event'):
    raise RuntimeError('Explicit allowlisted browser family required')
spec = importlib.util.spec_from_file_location('qa04_browser_launcher', HERE.parent/'qa04/run.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
original = launcher.clean_environment

def environment(root):
    env = original(root)
    env['PYTHONPATH'] = str(HERE/('browser_'+family+'_bridge')) + os.pathsep + env['PYTHONPATH']
    return env

launcher.clean_environment = environment
sys.exit(launcher.main())
