from pathlib import Path
import json,subprocess,os,re
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';prior=json.loads((O/'evidence/javascript-full.json').read_text());rows=[]
for item in prior:
 if item['exit']==0 or item['file'] in ['scripts/test_localized_place_urls.cjs','scripts/test_review_submission.cjs','scripts/test_review_cooldown.cjs']:continue
 cmd=['npx','--yes','--package','node@24','node','--test','--test-reporter=tap',str(R/item['file'])];env={**os.environ,'NODE_PATH':str(R/'.tmp/phone-dom/node_modules'),'KIDSMAP_JSDOM':str(R/'.tmp/phone-dom/node_modules/jsdom')}
 p=subprocess.run(cmd,cwd=R,env=env,capture_output=True,text=True);raw=p.stdout+p.stderr;(Q/(Path(item['file']).name+'.retry.log')).write_text(raw);rows.append({'file':item['file'],'command':cmd,'exit':p.returncode,'TAP_counts':dict(re.findall(r'^# (tests|pass|fail|skipped) (\d+)$',raw,re.M))});print(item['file'],p.returncode,flush=True)
(O/'evidence/javascript-env-retry.json').write_text(json.dumps(rows,indent=2))
