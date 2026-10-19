import sys,json
sys.argv=['runtime.py','testdb-probe'];from runtime import *
from django.db import transaction,connection
name=settings.DATABASES['default']['TEST']['NAME'];assert name=='test_m09s12_fix_r1'
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute('SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname=%s)',[name]);exists=c.fetchone()[0]
(QA/'testdb-entry.json').write_text(json.dumps({'own_named_test_db':name,'existed_before':exists,'normal_qa_db':'m09full_r1'},indent=2));assert not exists,'Test DB name already occupied; do not reuse blindly'
print(json.dumps({'own_named_test_db_absent':True}))
