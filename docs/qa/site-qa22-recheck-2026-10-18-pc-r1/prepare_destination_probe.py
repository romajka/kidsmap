import json,socket,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');F=R/'docs/qa/site-qa08-followup-fix-2026-10-18-pc-r1';O=Path(__file__).resolve().parent;Q=R/'.tmp/site22-pc-plan-r1'
def adapt(s):
 for a,b in [('site08-pc-followup-r1','site22-pc-plan-r1'),('site-qa08-followup-fix-2026-10-18-pc-r1','site-qa22-recheck-2026-10-18-pc-r1'),('m10s08_followup_r1','m10s22_plan_r1'),('m10s08-followup-r1','m10s22-plan-r1'),('33590','33600')]:s=s.replace(a,b)
 return s
with socket.socket() as s:s.bind(('127.0.0.1',33600))
for name in ['seed.py','test_site19_candidate.py','proxy.py','playwright.json']:(Q/name).write_text(adapt((F/name).read_text()))
for name in ['start_server.py','browser_driver.py']:(O/name).write_text(adapt((F/name).read_text()))
(O/'png').mkdir()
cmd=['docker','exec','m10s22-plan-r1-app','python',str(Q/'runtime.py'),'migrate'];r=subprocess.run(cmd,capture_output=True,text=True);(Q/'normal-migrate.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr[-500:]
(O/'evidence/destination-setup.json').write_text(json.dumps({'command':cmd,'exit':r.returncode,'purpose':'New own normal DB foundation for labelled transport+temporary CSS destination prototype; no candidate application','loopback':33600},indent=2));print('Destination probe own normal DB ready33600')
