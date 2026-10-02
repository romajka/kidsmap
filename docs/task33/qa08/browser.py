#!/usr/bin/env python3
"""Run the unchanged disposable QA04 launcher with bounded loopback UI bridge."""
import importlib.util,os,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('qa04_browser_launcher',HERE.parent/'qa04/run.py');launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(launcher)
original=launcher.clean_environment
def environment(root):
    env=original(root);env['PYTHONPATH']=str(HERE/'browser_bridge')+os.pathsep+env['PYTHONPATH'];return env
launcher.clean_environment=environment
sys.exit(launcher.main())
