import subprocess,os,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
labels=['catalog.testcases.test_task33_publication','catalog.testcases.test_task33_permissions','catalog.testcases.place_readiness','catalog.testcases.test_public_filter_consistency','catalog.testcases.test_task33_admin_editors']
cmd=[str(R/'.venv/Scripts/python.exe'),str(P/'run.py'),'test',*labels];env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8');r=subprocess.run(cmd,cwd=R,capture_output=True,encoding='utf-8',errors='replace',env=env)
(P/'tests-extra.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8');(P/'tests-extra-command.json').write_text(json.dumps({'command':cmd,'exit_code':r.returncode},indent=2),encoding='utf-8');print('exit',r.returncode);print((r.stdout+'\n'+r.stderr)[-2500:]);sys.exit(r.returncode)
