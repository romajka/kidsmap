"""Fictional prerequisite fixtures only; all checked removals use browser UI."""
import io,json
from pathlib import Path
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from catalog.models import Activity,OfferingGroup,PricingPlan,SiteSettings
from catalog.testcases.utils import create_ready_place
P=Path(__file__).resolve().parent;S=P.parents[2]/'.tmp'/P.name
password=json.loads((S/'credentials.json').read_text())['owner_password']
actors={}
for role in ['owner','admin','outsider']:
 actors[role]=get_user_model().objects.create_user('offerqa01_'+role,email='offerqa01_'+role+'@example.invalid',password=password,is_staff=role=='admin',is_superuser=role=='admin')
b=io.BytesIO();Image.new('RGB',(900,600),'#62a68b').save(b,format='PNG')
cells=[]
for lang in ['ru','az','en']:
 for width in [360,390,768,1024,1280,1440]:
  key=f'{lang}-{width}'
  place=create_ready_place(owner=actors['owner'],created_by=actors['owner'],name='Fictional OFFER01 '+key,name_az='Uydurma OFFER01 '+key,name_ru='Вымышленное OFFER01 '+key,name_en='Fictional OFFER01 '+key,city='baku',district='baku_yasamal',schedule_mode='always_open',price_mode='tariffs')
  place.photo.save('fictional-offer01-'+key+'.png',ContentFile(b.getvalue()),save=True)
  PricingPlan.objects.filter(place=place).delete()
  activity=Activity.objects.create(place=place,name_az='Uydurma OFFER01 '+key,name_ru='Вымышленное OFFER01 '+key,name_en='Fictional OFFER01 '+key,category=place.category,subcategory=place.subcategory,status='published')
  groups=[]
  for label,price in [('KEEP','20'),('REMOVE','80')]:
   group=OfferingGroup.objects.create(activity=activity,name_az=label+' '+key,name_ru=label+' '+key,name_en=label+' '+key,age_from=6,age_to=12)
   plan=PricingPlan.objects.create(offering_group=group,product_type='lesson',price=price,quantity=1,quantity_unit='lesson')
   groups.append({'group':group.pk,'plan':plan.pk,'label':label+' '+key})
  cells.append({'lang':lang,'width':width,'place':place.pk,'activity':activity.pk,'groups':groups})
(P/'fixtures.json').write_text(json.dumps({'cells':cells,'users':{k:{'username':u.username,'email':u.email} for k,u in actors.items()}},ensure_ascii=False,indent=2))
print(json.dumps({'fictional_places':len(cells),'roles':len(actors)}))
