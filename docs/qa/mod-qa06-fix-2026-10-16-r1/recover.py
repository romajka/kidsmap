import json,runpy,sys,subprocess
from pathlib import Path
h=Path(__file__).resolve().parent;r=h.parents[2];s=r/'.tmp'/h.name;cfg=json.loads((s/'config.json').read_text());entry=json.loads((h/'entry.json').read_text());server=json.loads((h/'server-current.json').read_text());info=json.loads(subprocess.check_output(['docker','inspect',cfg['container']],text=True))[0];assert info['Id']==(r/'docs/qa/mod-qa03-columns-fix-2026-10-16-r1/docker-start.txt').read_text().strip()and info['State']['Running']
report={'event':'Turn explicitly interrupted; pending exec IDs unknown and child processes gone','own_http_present':(Path('/proc')/str(server['pid'])).exists(),'foreign_http':[{'pid':p['pid'],'present':(Path('/proc')/str(p['pid'])).exists()}for p in entry['foreign_processes']],'owned_pg_same_id_running':True,'foreign_restart_performed':False,'continuity':'NOT VERIFIED across interruption'}
sys.argv=[str(h/'runtime.py'),'runtime-info'];runpy.run_path(str(h/'runtime.py'),run_name='__main__')
from django.db import connection
from django.conf import settings
testname=settings.DATABASES['default']['TEST']['NAME'];assert testname=='test_mod06_i18n_fix_r1'
with connection.cursor()as c:
 c.execute('SELECT count(*) FROM pg_database WHERE datname=%s',[testname]);report['own_testdb_exists']=bool(c.fetchone()[0]);c.execute('SELECT count(*) FROM pg_stat_activity WHERE datname=%s',[testname]);report['own_testdb_connections']=c.fetchone()[0]
assert report['own_testdb_connections']==0;connection.close();(h/'interruption.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
