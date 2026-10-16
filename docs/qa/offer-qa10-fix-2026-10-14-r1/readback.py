import json
from pathlib import Path
import psycopg
P=Path(__file__).resolve().parent;S=P.parents[2]/'.tmp/module05-full-2026-10-14-r1';cfg=json.loads((S/'config.json').read_text());sec=json.loads((S/'credentials.json').read_text());assert cfg['database']=='module05full_20261014_r1'
with psycopg.connect(host='127.0.0.1',port=cfg['pg_port'],dbname=cfg['database'],user=cfg['user'],password=sec['db_password']) as db:
 with db.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
  c.execute('SELECT p.product_type,p.price,p.currency,g.lesson_format FROM catalog_pricingplan p JOIN catalog_offeringgroup g ON g.id=p.offering_group_id JOIN catalog_activity a ON a.id=g.activity_id WHERE a.place_id=2 AND a.archived_at IS NULL AND g.archived_at IS NULL');live=c.fetchall();assert len(live)==1 and live[0][1]==20
  c.execute("SELECT status,payload->'nested_pricing' FROM catalog_volunteerplacerevision WHERE place_id=2");status,payload=c.fetchone();candidate=payload['activities'][0]['groups'][0]['pricing_plans'][0]['product_type'];assert candidate=='membership',candidate
 d={'transaction':'READ ONLY','live':[{'product_type':r[0],'price':str(r[1]),'currency':r[2],'group_format':r[3]} for r in live],'candidate_status':status,'candidate_product_type':candidate,'not_live_written_by_failed_selection':True,'own_database':cfg['database']}
(P/'readback.json').write_text(json.dumps(d,indent=2));print('PASS: live price20 unchanged; saved candidate stillmembership despite native Tour choice')
