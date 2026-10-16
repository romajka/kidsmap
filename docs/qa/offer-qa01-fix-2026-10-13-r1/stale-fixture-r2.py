import io,json
from pathlib import Path
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from catalog.models import Activity,OfferingGroup,PricingPlan
from catalog.testcases.utils import create_ready_place
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());owner=get_user_model().objects.get(username=F['users']['owner']['username'])
b=io.BytesIO();Image.new('RGB',(900,600),'#68a2ad').save(b,format='PNG');extras=[]
for key in ['stale-conflict-r2']:
 place=create_ready_place(owner=owner,created_by=owner,name='Fictional OFFER01 '+key,name_az='Uydurma OFFER01 '+key,city='baku',district='baku_yasamal',schedule_mode='always_open',price_mode='tariffs')
 place.photo.save('fictional-extra-'+key+'.png',ContentFile(b.getvalue()),save=True);PricingPlan.objects.filter(place=place).delete()
 a=Activity.objects.create(place=place,name_az='Uydurma OFFER01 '+key,category=place.category,subcategory=place.subcategory,status='published')
 groups=[]
 for label,price in [('KEEP','20'),('REMOVE','80')]:
  g=OfferingGroup.objects.create(activity=a,name_az=label+' '+key,age_from=6,age_to=12)
  plan=PricingPlan.objects.create(offering_group=g,product_type='lesson',price=price,quantity=1,quantity_unit='lesson')
  groups.append({'group':g.pk,'plan':plan.pk,'label':label+' '+key})
 extras.append({'key':key,'place':place.pk,'activity':a.pk,'groups':groups})
F['extras_history']=F['extras'];F['extras']=[x for x in F['extras'] if x['key']=='admin-import']+[{**x,'key':'stale-conflict'} for x in extras];(P/'fixtures.json').write_text(json.dumps(F,ensure_ascii=False,indent=2))
print(json.dumps({'additional_fictional_prerequisites':len(extras)}))
