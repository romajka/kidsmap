import io,json
from pathlib import Path
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from catalog.models import Activity,OfferingGroup,PricingPlan
from catalog.testcases.utils import create_ready_place
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());owner=get_user_model().objects.get(username=F['users']['owner']['username'])
b=io.BytesIO();Image.new('RGB',(900,600),'#65a898').save(b,format='PNG')
place=create_ready_place(owner=owner,created_by=owner,name='Fictional OFFER03 recheck',name_az='Uydurma OFFER03',name_ru='Вымышленное OFFER03',name_en='Fictional OFFER03',city='baku',district='baku_yasamal',schedule_mode='always_open',price_mode='tariffs')
place.photo.save('fictional-offer03.png',ContentFile(b.getvalue()),save=True);PricingPlan.objects.filter(place=place).delete()
ids=[]
for ai in range(2):
 a=Activity.objects.create(place=place,name_az=f'Uydurma activity {ai}',category=place.category,subcategory=place.subcategory,status='published')
 for gi in range(2):
  g=OfferingGroup.objects.create(activity=a,name_az=f'Uydurma group {ai}-{gi}',age_from=6,age_to=12)
  for pi in range(2):
   t=PricingPlan.objects.create(offering_group=g,product_type='lesson',price='20')
   ids.append({'ai':ai,'gi':gi,'pi':pi,'activity':a.pk,'group':g.pk,'plan':t.pk})
F.update(place=place.pk,cells=ids);(P/'fixtures.json').write_text(json.dumps(F,ensure_ascii=False,indent=2));print(json.dumps({'fictional_place':place.pk,'activities':2,'groups':4,'plans':8}))
