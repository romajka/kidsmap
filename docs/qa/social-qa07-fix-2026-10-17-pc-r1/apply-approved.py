import hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social07-pc-fix-r1';P=R/'docs/qa/social-qa07-recheck-2026-10-17-pc-r1';O=R/'docs/qa/social-qa07-fix-2026-10-17-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((Q/'entry.json').read_text());assert all(sha(R/p)==h for p,h in e['sources'].items())
subprocess.run(['git','apply','--ignore-space-change','--check',str(P/'proposed.diff')],cwd=R,check=True);subprocess.run(['git','apply','--ignore-space-change',str(P/'proposed.diff')],cwd=R,check=True)
sources={p:sha(R/p) for p in e['sources']};sources['src/catalog/testcases/test_social_qa07_activity_review_title.py']=sha(R/'src/catalog/testcases/test_social_qa07_activity_review_title.py');assert [p for p in e['sources'] if sources[p]!=e['sources'][p]]==['src/catalog/controllers/typed_reviews.py']
assert (R/'src/catalog/testcases/test_social_qa07_activity_review_title.py').read_text()==(P/'candidate_tests.py').read_text();assert (R/'src/catalog/controllers/typed_reviews.py').read_text()==(P/'candidate-typed_reviews.py').read_text()
(Q/'expected-source.json').write_text(json.dumps({'phase':'SOCIAL07-FIX','sources':sources},indent=2));(O/'source-applied.json').write_text(json.dumps({'sources':sources},indent=2))
subprocess.run(['docker','run','-d','--name','m09s07-fix-r1-app','--label','codex.owner=social07-pc-fix-r1','--network','m09s07-plan-r1-net','--read-only','--tmpfs','/tmp','-v',str(R)+':'+str(R)+':ro','-v',str(Q)+':'+str(Q)+':rw','-w',str(Q),'--entrypoint','python','bb90c815dc2b','-c','import time; time.sleep(86400)'],check=True,stdout=subprocess.DEVNULL)
print('Approved exact patch applied; 1022 source files, 1020 prior files unchanged; new isolated application created; prior containers',len(e['containers']))


