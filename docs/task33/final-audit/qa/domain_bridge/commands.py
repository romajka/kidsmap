"""Migrations/guards unchanged; only external audit probe suite added."""
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('domain_base_commands',Path('/root/km-final-domain/docs/task33/qa04/commands.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
dump=base.dump
BaselineRunner=base.BaselineRunner
def main(mode, labels):
    assert mode=='probe' and not labels
    result=base.main('probe',[])
    if result:return result
    runner=base.BaselineRunner(verbosity=1,interactive=False,parallel=1,keepdb=False)
    return runner.run_tests(['domain_probe.DomainCrossStageTests'])
