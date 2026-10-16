import io,json
from pathlib import Path
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from catalog.models import Activity,OfferingGroup,PricingPlan
from catalog.testcases.utils import create_ready_place
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());actors={'owner':get_user_model().objects.get(username=F['users']['owner']['username'])}
b=io.BytesIO();Image.new('RGB',(900,600),'#65a898').save(b,format='PNG');cells=[]
for lang in ['ru']:
 for width in [390]:
  key=f'new-plan-{lang}-{width}'
  place=create_ready_place(owner=actors['owner'],created_by=actors['owner'],name='Fictional OFFER02 '+key,name_az='Uydurma OFFER02 '+key,name_ru='Вымышленное OFFER02 '+key,name_en='Fictional OFFER02 '+key,city='baku',district='baku_yasamal',schedule_mode='always_open',price_mode='tariffs')
  place.photo.save('fictional-offer02-'+key+'.png',ContentFile(b.getvalue()),save=True);PricingPlan.objects.filter(place=place).delete()
  a=Activity.objects.create(place=place,name_az='Uydurma OFFER02 '+key,category=place.category,subcategory=place.subcategory,status='published')
  g=OfferingGroup.objects.create(activity=a,name_az='Uydurma OFFER02 group '+key,age_from=6,age_to=12)
  plan=PricingPlan.objects.create(offering_group=g,product_type='lesson',price='20')
  cells.append({'lang':lang,'width':width,'place':place.pk,'activity':a.pk,'group':g.pk,'plan':plan.pk})
F['new_cell']=cells[0];(P/'fixtures.json').write_text(json.dumps(F,ensure_ascii=False,indent=2));print(json.dumps({'own_optional_cells':len(cells)}))
