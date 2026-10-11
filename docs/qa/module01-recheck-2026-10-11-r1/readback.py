"""Read only this run's fictional Place; never perform audited transitions."""
import sys,json
sys.argv=['run.py','qa-state'];from run import *
from django.db import transaction,connection
from catalog.models import Place
with transaction.atomic():
 with connection.cursor() as cur:
  cur.execute('SET TRANSACTION READ ONLY');cur.execute("SET LOCAL statement_timeout='10s'");cur.execute("SET LOCAL lock_timeout='2s'")
 places=[];urls={lang:{'places':{}} for lang in ['ru','az','en']}
 from django.utils import translation
 for p in Place.objects.filter(pk__in=[1,2]):
  places.append({'id':p.pk,'name_az':p.name_az,'name_en':p.name_en,'name_ru':p.name_ru,'status':p.status,'is_active':p.is_active,'address':p.address,'city':p.city,'district':p.district,'lat':str(p.lat),'lng':str(p.lng),'nature':p.nature,'scalar':[str(p.price_from),str(p.price_to)],'plans':list(p.pricing_plan_records.values('id','price','title_az'))})
  for lang in urls:
   with translation.override(lang):urls[lang]['places'][str(p.pk)]=p.get_absolute_url()
 (HERE/'card-urls.json').write_text(json.dumps(urls,ensure_ascii=False,indent=2),encoding='utf-8')
 (HERE/'readback.json').write_text(json.dumps(places,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
 print('Read-only fictional Place readback saved; count',len(places))
