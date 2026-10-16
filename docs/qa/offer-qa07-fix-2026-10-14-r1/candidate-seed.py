import io,json
from pathlib import Path
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from catalog.models import Activity,OfferingGroup,PricingPlan
from catalog.testcases.utils import create_ready_place
P=Path('/home/ramin/kidsmap/docs/qa/offer-qa07-fix-2026-10-14-r1');password=json.loads(Path('/home/ramin/kidsmap/.tmp/offer-qa07-fix-2026-10-14-r1/credentials.json').read_text())['owner_password']
owner=get_user_model().objects.get(username='offerqa07_owner')
place=create_ready_place(owner=owner,created_by=owner,name='Fictional OFFER07',name_az='Uydurma OFFER07',name_ru='Вымышленное OFFER07',name_en='Fictional OFFER07',city='baku',district='baku_yasamal',schedule_mode='always_open',price_mode='tariffs');b=io.BytesIO();Image.new('RGB',(900,600),'#65a898').save(b,format='PNG');place.photo.save('offer07-candidate-only.png',ContentFile(b.getvalue()),save=True);PricingPlan.objects.filter(place=place).delete()
a=Activity.objects.create(place=place,name_az='BASE OFFER07 activity',category=place.category,subcategory=place.subcategory,status='published');g=OfferingGroup.objects.create(activity=a,name_az='Fictional OFFER07 group',age_from=6,age_to=12);plan=PricingPlan.objects.create(offering_group=g,product_type='lesson',price='20')
old=json.loads((P/'fixtures.json').read_text());old['candidate_only']={'place':place.pk,'activity':a.pk,'group':g.pk,'plan':plan.pk}
(P/'fixtures.json').write_text(json.dumps(old,indent=2));print('New fictional OFFER07 fixture only; accepted01–06 fixtures untouched.')
