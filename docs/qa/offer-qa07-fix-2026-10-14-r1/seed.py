import io,json
from pathlib import Path
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from catalog.models import Activity,OfferingGroup,PricingPlan
from catalog.testcases.utils import create_ready_place
P=Path('/home/ramin/kidsmap/docs/qa/offer-qa07-fix-2026-10-14-r1');password=json.loads(Path('/home/ramin/kidsmap/.tmp/offer-qa07-fix-2026-10-14-r1/credentials.json').read_text())['owner_password']
U=get_user_model();owner=U.objects.create_user('offerqa07_owner',email='offerqa07_owner@example.invalid',password=password);admin=U.objects.create_user('offerqa07_admin',email='offerqa07_admin@example.invalid',password=password,is_staff=True,is_superuser=True)
place=create_ready_place(owner=owner,created_by=owner,name='Fictional OFFER07',name_az='Uydurma OFFER07',name_ru='Вымышленное OFFER07',name_en='Fictional OFFER07',city='baku',district='baku_yasamal',schedule_mode='always_open',price_mode='tariffs');b=io.BytesIO();Image.new('RGB',(900,600),'#65a898').save(b,format='PNG');place.photo.save('offer07-fictional.png',ContentFile(b.getvalue()),save=True);PricingPlan.objects.filter(place=place).delete()
a=Activity.objects.create(place=place,name_az='BASE OFFER07 activity',category=place.category,subcategory=place.subcategory,status='published');g=OfferingGroup.objects.create(activity=a,name_az='Fictional OFFER07 group',age_from=6,age_to=12);plan=PricingPlan.objects.create(offering_group=g,product_type='lesson',price='20')
(P/'fixtures.json').write_text(json.dumps({'place':place.pk,'activity':a.pk,'group':g.pk,'plan':plan.pk,'owner_email':owner.email,'admin_username':admin.username},indent=2));print('New fictional OFFER07 fixture only; accepted01–06 fixtures untouched.')
