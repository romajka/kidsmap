from django.db import connection,transaction
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
allowed={'test_qa14_20261012_r1'}|{f'test_qa14_20261012_r1_{i}' for i in range(1,5)}|{'test_qa14_module01_final_20261012_r1'}|{f'test_qa14_module01_final_20261012_r1_{i}' for i in range(1,5)}
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
  c.execute("SELECT datname,(SELECT count(*) FROM pg_stat_activity a WHERE a.datname=d.datname) FROM pg_database d WHERE datname LIKE 'test_qa14_%'")
  rows=c.fetchall()
assert all(name in allowed and active==0 for name,active in rows)
# Only this run's disposable failed-attempt TEST DBs, no runtime stand DB.
connection.set_autocommit(True)
with connection.cursor() as c:
 c.execute("SET statement_timeout='10s'");c.execute("SET lock_timeout='2s'")
 for name,active in rows:c.execute('DROP DATABASE "'+name+'"')
(HERE/'testdb-cleanup.json').write_text(json.dumps({'owned_inactive_test_dbs_removed':[name for name,_ in rows],'runtime_databases_untouched':True}))
print('Own inactive TEST DB cleanup:',len(rows))
