import subprocess,sys,json,os
from pathlib import Path
here=Path(__file__).resolve().parent
env=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONUTF8='1')
labels=['catalog.testcases.place_readiness','catalog.testcases.test_admin_candidate_cover','catalog.testcases.test_task33_place_continuous','catalog.testcases.photo_workflow','catalog.testcases.test_place_json_and_pricing_modes']
with (here/'backend-repeat.txt').open('w',encoding='utf-8') as out:
    result=subprocess.run([sys.executable,str(here/'run.py'),'test',*labels],stdout=out,stderr=subprocess.STDOUT,env=env)
(here/'backend-result.json').write_text(json.dumps({'command':[sys.executable,str(here/'run.py'),'test',*labels],'exit_code':result.returncode,'reason_for_repeat':'First PowerShell redirection returned shell exit 1 despite unittest OK; capture native exit explicitly.'},indent=2),encoding='utf-8')
print('Native test exit',result.returncode)
