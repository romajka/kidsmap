import json,os
from pathlib import Path
import psycopg
h=Path(__file__).resolve().parent;r=h.parents[2];s=r/'.tmp'/h.name;cfg=json.loads((s/'config.json').read_text());secret=json.loads((s/'credentials.json').read_text());assert cfg['database']=='mod08_plan_r1'
with psycopg.connect(host='127.0.0.1',port=cfg['pg_port'],user=cfg['user'],password=secret['db_password'],dbname=cfg['database'],connect_timeout=5)as con:
 with con.cursor()as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");out={}
  for name in ['django_migrations','auth_user','catalog_event','catalog_specialist']:
   c.execute('SELECT to_regclass(%s)',[name]);exists=bool(c.fetchone()[0])
   if exists:
    from psycopg import sql
    c.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(name)));out[name]=c.fetchone()[0]
  (h/'db-recovery-counts.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
