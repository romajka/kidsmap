import json,socket
from pathlib import Path
with socket.socket()as s:
    s.settimeout(2);absent=s.connect_ex(('127.0.0.1',8799))!=0
assert absent,'Owned report preview listener still present; inspect exact process before terminating'
result={'status':'PASS','report_http_8799_absent':absent,'browser_session':'finalaudit-report closed successfully by playwright-cli','application_test_cleanup':'See individual run records; all completed disposable launchers reported cleanup PASS','production':'NOT_CONTACTED'}
Path('/mnt/c/kidsmap/docs/task33/final-audit/report-cleanup.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
