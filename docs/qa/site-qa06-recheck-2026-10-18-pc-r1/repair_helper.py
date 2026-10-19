import json
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site06-pc-plan-r1'
p=O/'start_browser.py';s=p.read_text().replace('qa/site15/state/','qa/site06/state/')
s=s.replace("old={}\nif stage=='green':", "old=json.loads((Q/'own-processes.json').read_text()) if (Q/'own-processes.json').exists() else {}\nif old:")
s=s.replace("if stage=='red':\n proxylog=", "if not old:\n proxylog=")
p.write_text(s)
(Q/'red-server-initial.log').write_bytes((Q/'red-server.log').read_bytes())
p=Q/'qa_urls.py';s=p.read_text().replace('isolated SITE15 plan DB','isolated SITE06 plan DB').replace("\n data['gallery']=", "\n  data['gallery']=");p.write_text(s)
(O/'evidence/readiness-adjustment.json').write_text(json.dumps({'initial_launcher_exit':1,'cause':'Copied own launcher polled stale QA helper path /qa/site15/state/404; server itself served current root200.','resolution':'Correct own /qa/site06/state/ endpoint and restart only verified own server; reuse existing own proxy. Gallery readback moved inside explicit read-only transaction. No application changes.'},indent=2))
print('Own helper/readiness corrected; initial evidence retained in ignored scratch')
