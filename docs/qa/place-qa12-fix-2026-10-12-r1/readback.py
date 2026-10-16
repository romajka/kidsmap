import json
from pathlib import Path
from django.conf import settings
from django.db import connection,transaction
from django.utils.translation import override
from catalog.models import Place
HERE=Path(__file__).resolve().parent
entities=json.loads((HERE/'entities.json').read_text());pk=entities['id'];pids=[pk]+entities.get('branch_ids',[])
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 data=[];urls={lang:{'places':{}} for lang in ('ru','az','en')}
 for p in Place.objects.filter(pk__in=pids):
  data.append({'id':p.pk,'name_az':p.name_az,'name_ru':p.name_ru,'name_en':p.name_en,'status':p.status,'address':p.address,'nature':p.nature,'schedule_mode':p.schedule_mode,'lat':str(p.lat),'lng':str(p.lng),'price_mode':p.price_mode,'prices':[str(p.price_from),str(p.price_to)],'photo':str(p.photo),'gallery':list(p.gallery.values('id','image','order')),'plans':list(p.pricing_plan_records.values('id','price','title_az'))})
  for lang in urls:
   with override(lang):urls[lang]['places'][str(p.pk)]=p.get_absolute_url()
 (HERE/'card-urls.json').write_text(json.dumps(urls));(HERE/'readback.json').write_text(json.dumps(data,ensure_ascii=False,default=str,indent=2))
 print('Read-only audited synthetic Place aggregates saved.')
