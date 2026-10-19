import json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/site-qa20-fix-2026-10-18-pc-r1';P=R/'docs/qa/site-qa22-fix-2026-10-18-pc-r1';Q=R/'.tmp/site20-pc-fix-r1'
def adapt(s):
 for a,b in [('site22-pc-fix-r1','site20-pc-fix-r1'),('site-qa22-fix-2026-10-18-pc-r1','site-qa20-fix-2026-10-18-pc-r1'),('m10s22_fix_r1','m10s20_fix_r1'),('m10s22-fix-r1','m10s20-fix-r1'),('33610','33630')]:s=s.replace(a,b)
 return s
for n in ['browser-sentinels-red.js','browser-stale-email.js','browser-json-error-snapshots.js','browser-file-error-central.js','browser-neighbor-destinations.js','browser-console.js']:(O/n).write_text(adapt((P/n).read_text()))
s=adapt((P/'run_green_backend.py').read_text()).replace("labels=['catalog.testcases.test_site_qa22_save_exit'","labels=['catalog.testcases.test_site_qa20_permission_actions','catalog.testcases.test_site_qa22_save_exit'").replace('==114','==122').replace('test_m10s22_fix_green_r1','test_m10s20_fix_green_r1')
(O/'run_green_backend.py').write_text(s)
for cmd in [['python3',str(O/'run_red.py')],['python3',str(O/'normal_migrate.py')],['python3',str(O/'start_server.py'),'red'],['python3',str(O/'browser_driver.py'),'open','about:blank','--config='+str(Q/'playwright.json')],['python3',str(O/'browser_driver.py'),'browser-baseline.js'],['python3',str(O/'browser_driver.py'),'browser-sentinels-red.js']]:
 r=subprocess.run(cmd,capture_output=True,text=True)
 (Q/(cmd[-1].replace('/','_')[-70:]+'.log')).write_text(r.stdout+r.stderr)
 print(json.dumps({'command':cmd[:3]+cmd[3:],'exit':r.returncode,'tail':r.stdout[-220:]},ensure_ascii=False),flush=True)
 assert r.returncode==0,r.stderr[-1000:]
(O/'prepare.py').write_bytes(Path(__file__).read_bytes())
