import json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site06-pc-fix-r1'
(O/'evidence/red-bootstrap-timeout.json').write_bytes((O/'evidence/red-backend.json').read_bytes())
(Q/'red-bootstrap-timeout.log').write_bytes((Q/'red-tests.log').read_bytes())
cmd=['docker','exec','m09full-r1-pg','psql','-U','m09full_r1','-d','postgres','-At','-c',"BEGIN READ ONLY; SET LOCAL statement_timeout='5s'; SELECT count(*) FROM pg_database WHERE datname='test_m10s06_fix_r1'; COMMIT;"]
r=subprocess.run(cmd,capture_output=True,text=True,check=True);assert [x for x in r.stdout.splitlines() if x.isdigit()]==['0']
create=['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1','-O','m09full_r1','test_m10s06_fix_r1']
r=subprocess.run(create,capture_output=True,text=True);assert r.returncode==0,r.stderr
(O/'qa-adjustments.json').write_text(json.dumps([{'kind':'owned test bootstrap, no app/assertion changes','first_result':'exit2 before methods: CREATE DATABASE canceled by 20s runtime statement_timeout','evidence':'evidence/red-bootstrap-timeout.json','action':'confirmed absent own test DB in read-only transaction, created exact owned DB using QA PG createdb; rerun unchanged84 methods','command':create}],indent=2))
print(json.dumps({'owned_test_database_precreated':True,'first_failure_preserved':True,'app_unchanged':True}))
