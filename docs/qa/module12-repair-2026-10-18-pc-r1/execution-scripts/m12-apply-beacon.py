import sys,subprocess,json
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/m12-full-r1')
from stage_apply import *
S=O/'stages/beacon';(S/'evidence').mkdir(parents=True,exist_ok=True);cmd=['node',str(Q/'test_m12_sender_candidate.cjs'),str(R)];p=subprocess.run(cmd,capture_output=True,text=True);data=json.loads(p.stdout);assert p.returncode==1 and len(data['results'])==4 and [r['mode'] for r in data['results'] if not r['PASS']]==['rejected'];(S/'evidence/red-r1.json').write_text(json.dumps({'exit':p.returncode,'failures':['sendBeacon_false_has_no_fetch_fallback'],'errors':[],'command':cmd,'result':data},indent=2))
(S/'IMPLEMENTATION_PLAN.md').write_text('''# ANALYTICS-QA-15 — refused Beacon has no fallback

Fresh Node VM executes the actual sender function extracted from base.html:4cases, rejected-beacon caseFAIL, accepted/throws/missing controlsPASS. Existing sender returns unconditionally after sendBeacon even when it reports false. W3C primary API contract: https://www.w3.org/TR/beacon/#sendbeacon-method — false means the data could not be queued; true is queue acceptance, not proof of server delivery. No claim of a real production queue overflow.

Exactly two files: src/catalog/templates/base.html returns only if navigator.sendBeacon(trackUrl,blob) is true; otherwise falls through to the already existing same-origin keepalive fetch. Add scripts/test_analytics_sender.cjs exact tested VM regression. No taxonomy/payload/extra retry/event-policy change; accepted Beacon emits no duplicate fetch, throws/missing still use one existing fallback.

Acceptance:4Node sender behaviors; native SIMULATED false-return branch then real same-origin POST200 and delta+1, no duplicates. Original current-page native phone→directions problem is separate: diagnostic observes no second DOM click after unsupported tel navigation under headless Chromium, but fresh-page directions records1/200. Do not attribute that to rejected Beacon; independent next action uses a newly loaded page and preserves that limitation/evidence. Final fresh backend/UI regression on latest source, no real outbound contact/GA.
''')
path='src/catalog/templates/base.html';text=(R/path).read_bytes().decode();old='                navigator.sendBeacon(trackUrl, blob);\n                return;';new='                if (navigator.sendBeacon(trackUrl, blob)) return; // Enqueued'
if '\r\n' in text:old=old.replace('\n','\r\n');new=new.replace('\n','\r\n')
assert old in text;text=text.replace(old,new);files={path:text.encode(),'scripts/test_analytics_sender.cjs':(Q/'test_m12_sender_candidate.cjs').read_bytes()};apply('beacon',files,'stages/beacon/evidence/red-r1.json')
