"""Run only existing applicable module05 tests, keep exact native counts/exits."""
import subprocess,os,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
labels=['catalog.testcases.test_task33_program_workspace','catalog.testcases.test_task33_pricing','catalog.testcases.test_task33_public_details','catalog.testcases.test_organization_detach_transport','catalog.testcases.test_place_json_and_pricing_modes','catalog.testcases.pricing_plans_relational','catalog.testcases.pricing_plans','catalog.testcases.test_legacy_pricing_notes']
env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
cmd=[str(R/'.venv/Scripts/python.exe'),str(P/'run.py'),'test',*labels]
r=subprocess.run(cmd,cwd=R,capture_output=True,encoding='utf-8',errors='replace',env=env)
(P/'tests.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8')
(P/'tests-command.json').write_text(json.dumps({'command':cmd,'exit_code':r.returncode},indent=2),encoding='utf-8')
print('exit',r.returncode);print((r.stdout+'\n'+r.stderr)[-4500:]);sys.exit(r.returncode)
