import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Place
HERE=Path(__file__).resolve().parent
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
  own=Place.objects.filter(owner_id=2,status='draft',is_active=False).values_list('id',flat=True).first()
  foreign=Place.objects.exclude(owner_id=2).values_list('id',flat=True).first()
 (HERE/'acl-fixture-ids.json').write_text(json.dumps({'own_private_id':own,'foreign_id':foreign,'synthetic_only':True,'read_only':True}))
 print({'private_fixture_exists':own is not None,'foreign_fixture_exists':foreign is not None})
