"""Create only this run's disposable database on previously verified OWN PostgreSQL."""
import json,os
from pathlib import Path
import psycopg
from psycopg import sql
h=Path(__file__).resolve().parent;r=h.parents[2];s=r/'.tmp'/h.name
for k in list(os.environ):
 if k not in {'PATH','LANG','LC_ALL','TZ'}:os.environ.pop(k)
cfg=json.loads((s/'config.json').read_text());secret=json.loads((s/'credentials.json').read_text());assert cfg['database']=='mod08_plan_r1'and cfg['user']=='mod03_columns_fix_r1'and cfg['pg_port']==47955
with psycopg.connect(host='127.0.0.1',port=cfg['pg_port'],user=cfg['user'],password=secret['db_password'],dbname='postgres',autocommit=True)as con:
 with con.cursor()as c:
  c.execute('SELECT count(*) FROM pg_database WHERE datname=%s',[cfg['database']]);assert c.fetchone()[0]==0
  c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(cfg['database'])))
print(json.dumps({'created_own_database':cfg['database'],'existing_databases_modified':False}))
