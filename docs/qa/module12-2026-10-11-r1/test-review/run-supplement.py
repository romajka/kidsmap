"""Run own audit assertions through the parent's isolated test launcher."""
import runpy
import sys
import inspect  # Preload the stdlib before the root QA helper directory enters sys.path.
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.argv = [str(HERE.parent / 'run.py'), 'test', *(sys.argv[1:] or ['test_analytics_acceptance'])]
runpy.run_path(str(HERE.parent / 'run.py'), run_name='__main__')
