"""Unchanged targeted tests; sanitized evidence, native exit propagated."""
from pathlib import Path
import subprocess,json,re,datetime,os,sys
P=Path(__file__).resolve().parent;R=P.parents[2];sys.stdout.reconfigure(encoding='utf-8')
labels=['auth_flow','auth_access','test_email_verification_consumption','test_google_auth','test_account_deletion','test_task33_permissions','test_task33_ownership','test_organization_invitation_transport','test_volunteer_admin','test_volunteer_dashboard','test_task33_specialist_privacy','test_task33_specialist_security_review','test_task33_specialist_transfer']
cmd=[str(R/'.venv/Scripts/python.exe'),str(P/'run.py'),'test',*['catalog.testcases.'+s for s in labels]]
env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
r=subprocess.run(cmd,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env=env)
s=r.stdout+'\n'+r.stderr
s,n=re.subn(r'(name=["\']csrfmiddlewaretoken["\']\s+value=["\'])[^"\']+',r'\1[LOCAL-CSRF-REDACTED]',s)
s=re.sub(r'(/auth/reset/)[^/\s"<>]+/[^/\s"<>]+/',r'\1[UID]/[TOKEN]/',s)
s=re.sub(r'([?&]token=)[^&\s"<>]+',r'\1[REDACTED]',s)
(P/'tests.log').write_text(s,encoding='utf-8');(P/'tests-command.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'exit_code':r.returncode,'csrf_redactions':n},indent=2),encoding='utf-8')
print('Native exit',r.returncode)
for line in s.splitlines():
 if re.match(r'^(Ran |FAILED|OK|FAIL:|ERROR:|Found |System check)',line):print(line[:500])
sys.exit(r.returncode)
