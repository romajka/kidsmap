"""Fictional prerequisites only; checked pricing transitions are browser-driven."""
import io,json
from pathlib import Path
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from catalog.models import Activity,OfferingGroup,PricingPlan
from catalog.testcases.utils import create_ready_place
P=Path(__file__).resolve().parent;S=P.parents[2]/'.tmp'/P.name
password=json.loads((S/'credentials.json').read_text())['owner_password'];actors={}
for role in ['owner','admin','outsider']:
 actors[role]=get_user_model().objects.get(username='offerqa03_'+role)
b=io.BytesIO();Image.new('RGB',(900,600),'#65a898').save(b,format='PNG');cells=[]
for lang in ['ru','az','en']:
 for width in [360,390,768,1024,1280,1440]:
  key=f'{lang}-{width}'
  place=create_ready_place(owner=actors['owner'],created_by=actors['owner'],name='Fictional OFFER03 '+key,name_az='Uydurma OFFER03 '+key,name_ru='Вымышленное OFFER03 '+key,name_en='Fictional OFFER03 '+key,city='baku',district='baku_yasamal',schedule_mode='always_open',price_mode='tariffs')
  place.photo.save('fictional-offer03-'+key+'.png',ContentFile(b.getvalue()),save=True);PricingPlan.objects.filter(place=place).delete()
  for ai in range(2):
   a=Activity.objects.create(place=place,name_az=f'Uydurma activity {ai} '+key,category=place.category,subcategory=place.subcategory,status='published')
   for gi in range(2):
    g=OfferingGroup.objects.create(activity=a,name_az=f'Uydurma group {gi} '+key,age_from=6,age_to=12)
    for pi in range(2):
     plan=PricingPlan.objects.create(offering_group=g,product_type='lesson',price='20')
     if (ai,gi,pi)==(1,1,1):cells.append({'lang':lang,'width':width,'place':place.pk,'activity':a.pk,'group':g.pk,'plan':plan.pk})
(P/'fixtures.json').write_text(json.dumps({'cells':cells,'users':{k:{'username':u.username,'email':u.email} for k,u in actors.items()}},ensure_ascii=False,indent=2));print(json.dumps({'fictional_cells':len(cells),'own_roles':len(actors)}))
