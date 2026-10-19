import json,subprocess,shutil
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m12-full-r1';O=R/'docs/qa/module12-repair-2026-10-18-pc-r1';shutil.copyfile(O/'evidence/javascript.json',O/'evidence/javascript-node18.json');results=[]
for name,tail in [('sender',[str(R/'scripts/test_analytics_sender.cjs'),str(R)]),('ai-referral',[str(R/'static/js/tests/ai_referral_tracking.test.js')]),('phone-dom',['--test',str(R/'scripts/test_phone_reveal.cjs')])]:
 cmd=['npx','--yes','--package','node@24','node',*tail];p=subprocess.run(cmd,capture_output=True,text=True,cwd=R);(Q/(name+'-node24.log')).write_text(p.stdout+p.stderr);d={'name':name,'command':cmd,'exit':p.returncode}
 if name=='sender':d['result']=json.loads(p.stdout)
 else:d['summary']=[s for s in (p.stdout+p.stderr).splitlines() if s.startswith(('# tests','# pass','# fail','# skipped','AI referral'))]
 results.append(d)
(O/'evidence/javascript.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2));assert all(d['exit']==0 for d in results)
