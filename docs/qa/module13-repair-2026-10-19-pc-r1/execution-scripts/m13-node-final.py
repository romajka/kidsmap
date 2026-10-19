from pathlib import Path
import subprocess,json,os,re
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
excluded={'test_localized_place_urls.cjs','test_review_submission.cjs','test_review_cooldown.cjs'}
files=sorted([p for p in (R/'scripts').glob('test_*.cjs') if p.name not in excluded]+list((R/'scripts/tests').glob('*.test.cjs'))+list((R/'static/js/tests').glob('*.test.js')))
cmd=['npx','--yes','--package','node@24','node','--test','--test-reporter=tap',*[str(f) for f in files]];env={**os.environ,'NODE_PATH':str(R/'.tmp/phone-dom/node_modules'),'KIDSMAP_JSDOM':str(R/'.tmp/phone-dom/node_modules/jsdom')}
p=subprocess.run(cmd,cwd=R,env=env,capture_output=True,text=True);raw=p.stdout+p.stderr;(Q/'node-final.log').write_text(raw);d={'command':cmd,'exit':p.returncode,'unit_files':[f.relative_to(R).as_posix() for f in files],'excluded_native_files':sorted(excluded),'TAP_counts':dict(re.findall(r'^# (tests|pass|fail|skipped) (\d+)$',raw,re.M)),'native_acceptance':['stock-urls-r2.json','stock-review-submission-r2.json','stock-browser-scripts.json cooldown exit0'],'jsdom':'29.1.1','node':'24'};(O/'evidence/node-final.json').write_text(json.dumps(d,indent=2));print(json.dumps({k:v for k,v in d.items() if k not in ['command','unit_files']},indent=2))
