import json
from pathlib import Path
from django.utils.translation import gettext,override
from catalog.models import Activity
from django.db import transaction,connection
P=Path(__file__).resolve().parent;rows=[]
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 a=Activity.objects.get(pk=Activity.objects.filter(status='pending').values_list('pk',flat=True).first())
 for lang,label in [('ru','На проверке'),('az','Yoxlamadadır'),('en','Under review')]:
  with override(lang):
   for kind,actual in [('gettext',gettext('На проверке')),('model-display',a.get_status_display())]:rows.append({'id':lang+'-'+kind,'status':'PASS' if actual==label else 'FAIL','actual':actual,'expected':label})
(P/'pending-check.json').write_text(json.dumps({'rows':rows},ensure_ascii=False,indent=2));assert all(x['status']=='PASS' for x in rows),rows;print('Pending ordinary gettext and actual Activity display PASS',len(rows))
