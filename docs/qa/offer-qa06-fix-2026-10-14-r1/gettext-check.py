import json
from pathlib import Path
from django.utils.translation import gettext,override
from django.db import connection,transaction
from catalog.models import Place
from catalog.services.pricing_plans import offering_editor_choices
P=Path(__file__).resolve().parent;vals=json.loads((P/'translations.json').read_text());f=json.loads((P/'fixtures.json').read_text());rows=[]
def check(id,actual,expected):
 rows.append({'id':id,'actual':actual,'expected':expected,'status':'PASS' if actual==expected else 'FAIL'})
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 place=Place.objects.get(pk=f['owner_cells'][0]['place'])
 for lang in ['ru','az','en']:
  with override(lang):
   for key,v in vals.items():check(lang+'-'+key,gettext(key),key if lang=='ru' else v[lang])
   choices=offering_editor_choices(place)
   for typ,code,key in [('charge_roles','primary','Основной'),('charge_roles','addon','Дополнительный'),('charge_roles','registration_fee','Регистрационный взнос'),('billing_modes','one_time','Разовая оплата'),('billing_modes','recurring','Регулярная оплата'),('billing_modes','installment','Оплата частями'),('product_types','registration_fee','Регистрационный взнос')]:check(lang+'-'+typ+'-'+code,dict(choices[typ])[code],key if lang=='ru' else vals[key][lang])
   key='Публикация занятия: %(status)s';check(lang+'-placeholder',gettext(key)%{'status':'X'},(key if lang=='ru' else vals[key][lang])%{'status':'X'})
(P/'gettext-check.json').write_text(json.dumps({'rows':rows},ensure_ascii=False,indent=2));assert all(x['status']=='PASS' for x in rows),[x for x in rows if x['status']=='FAIL'];print('Real Django/gettext/service checks PASS',len(rows))
