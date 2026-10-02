#!/usr/bin/env python3
"""Stage 12 local browser bridge on the disposable QA04 PostgreSQL launcher."""
import importlib.util
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
LAUNCHER = HERE.parents[1] / "qa04" / "run.py"
spec = importlib.util.spec_from_file_location("qa04_browser_launcher", LAUNCHER)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
original = launcher.clean_environment


def environment(root):
    env = original(root)
    env["PYTHONPATH"] = str(HERE / "browser_bridge") + os.pathsep + env["PYTHONPATH"]
    return env


launcher.clean_environment = environment
sys.exit(launcher.main())
