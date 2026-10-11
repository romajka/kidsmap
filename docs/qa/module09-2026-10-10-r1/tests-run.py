from pathlib import Path
import subprocess,json,re,datetime,os,sys,time
P=Path(__file__).resolve().parent;R=P.parents[2];sys.stdout.reconfigure(encoding='utf-8')
labels=['test_task33_reviews','test_task33_review_independent','test_review_confirmation','test_place_review_cooldown','test_favorite_metrics','test_public_favorite_count','test_task33_notifications','test_task33_notification_crashes']
cmd=[str(R/'.venv/Scripts/python.exe'),str(P/'run.py'),'test',*['catalog.testcases.'+s for s in labels]]
env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8');start=time.monotonic()
r=subprocess.run(cmd,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env=env)
s=r.stdout+'\n'+r.stderr
s,n=re.subn(r'(name=["\']csrfmiddlewaretoken["\']\s+value=["\'])[^"\']+',r'\1[LOCAL-CSRF-REDACTED]',s)
s=re.sub(r'([?&]token=)[^&\s"<>]+',r'\1[REDACTED]',s)
(P/'tests.log').write_text(s,encoding='utf-8');(P/'tests-command.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'exit_code':r.returncode,'csrf_redactions':n,'duration_seconds':round(time.monotonic()-start,2)},indent=2),encoding='utf-8')
print('Native exit',r.returncode)
for line in s.splitlines():
 if re.match(r'^(Ran |FAILED|OK|FAIL:|ERROR:|Found |System check)',line):print(line[:300])
sys.exit(r.returncode)
