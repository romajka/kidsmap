import json,os,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent
labels=['test_specialist_proposal_drafts','test_specialist_entry_locations','test_specialist_entry_admin','test_task33_specialist_workspace','test_task33_specialist_screens_security','test_task33_specialist_privacy','test_task33_specialist_domain','test_task33_specialist_security_review']
command=[sys.executable,str(P/'run.py'),'test',*['catalog.testcases.'+x for x in labels]]
start=time.monotonic();env={**os.environ,'PYTHONIOENCODING':'utf-8','PYTHONUTF8':'1'}
r=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',env=env)
(P/'backend.txt').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8')
(P/'backend-result.json').write_text(json.dumps({'command':command,'exit_code':r.returncode,'seconds':round(time.monotonic()-start,3)},indent=2),encoding='utf-8')
print('Native test exit',r.returncode);print((r.stdout+'\n'+r.stderr)[-1200:].encode('ascii','backslashreplace').decode())
