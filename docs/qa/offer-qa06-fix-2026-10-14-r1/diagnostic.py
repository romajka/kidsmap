import json
from pathlib import Path
from django.utils.translation import gettext,override
from catalog.models import Activity
from django.db import transaction,connection
P=Path(__file__).resolve().parent
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 for l in ['ru','az','en']:
  with override(l):print(json.dumps({'lang':l,'gettext':gettext('На проверке'),'choices':[(v,str(t),type(t).__name__,repr(t)) for v,t in Activity._meta.get_field('status').choices],'displays':[a.get_status_display() for a in Activity.objects.filter(status='pending')]},ensure_ascii=False))
