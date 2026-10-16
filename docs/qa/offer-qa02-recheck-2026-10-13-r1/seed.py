"""New fictional prerequisites in the previously owned isolated QA DB only."""
import io,json
from pathlib import Path
from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from catalog.models import Activity,OfferingGroup,PricingPlan
from catalog.testcases.utils import create_ready_place
P=Path(__file__).resolve().parent
owner=get_user_model().objects.get(username='offerqa01_owner')
place=create_ready_place(owner=owner,created_by=owner,name='Fictional OFFER02 recheck',name_az='Uydurma OFFER02 recheck',city='baku',district='baku_yasamal',schedule_mode='always_open',price_mode='tariffs')
b=io.BytesIO();Image.new('RGB',(900,600),'#64a198').save(b,format='PNG');place.photo.save('fictional-offer02-recheck.png',ContentFile(b.getvalue()),save=True);PricingPlan.objects.filter(place=place).delete()
a=Activity.objects.create(place=place,name_az='Uydurma OFFER02 activity',category=place.category,subcategory=place.subcategory,status='published')
g=OfferingGroup.objects.create(activity=a,name_az='Uydurma OFFER02 group',age_from=6,age_to=12)
plan=PricingPlan.objects.create(offering_group=g,product_type='lesson',price='20')
(P/'fixtures.json').write_text(json.dumps({'place':place.pk,'activity':a.pk,'group':g.pk,'plan':plan.pk,'owner_email':owner.email,'fictional':True}))
print(json.dumps({'own_new_fictional_place':place.pk}))
