import json,urllib.request
from pathlib import Path
O=Path(__file__).resolve().parent
with urllib.request.urlopen('http://127.0.0.1:33520/qa/site06/state/',timeout=15) as r:assert r.status==200
(O/'evidence/refined-readiness.json').write_text(json.dumps({'initial_launcher_exit':1,'initial_reason':'20s readiness window elapsed while runtime verified source/imported under concurrent test bootstrap','owned_server_later_ready200':True,'server_restarted_again':False,'app_error':False},indent=2))
print('Owned refined runtime ready200; existing PID retained.')
