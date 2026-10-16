import io,json
from pathlib import Path
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from catalog.models import Activity,OfferingGroup,PricingPlan
from catalog.testcases.utils import create_ready_place
P=Path(__file__).resolve().parent;R=P.parents[2];sec=json.loads((R/'.tmp'/P.name/'credentials.json').read_text());U=get_user_model()
owner=U.objects.create_user('offerqa09fix_owner',email='offerqa09fix_owner@example.invalid',password=sec['owner_password']);admin=U.objects.create_superuser('offerqa09fix_admin',email='offerqa09fix_admin@example.invalid',password=sec['owner_password'])
place=create_ready_place(owner=owner,created_by=owner,name='Fictional OFFER09',name_az='Uydurma OFFER09',name_ru='Вымышленное OFFER09',name_en='Fictional OFFER09',city='baku',district='baku_yasamal',schedule_mode='always_open',price_mode='tariffs',price_from=None,price_to=None)
b=io.BytesIO();Image.new('RGB',(900,600),'#65a898').save(b,format='PNG');place.photo.save('offer09-fictional.png',ContentFile(b.getvalue()),save=True);PricingPlan.objects.filter(place=place).delete()
a=Activity.objects.create(place=place,name_az='Fictional OFFER09 activity',category=place.category,subcategory=place.subcategory,status='published');g=OfferingGroup.objects.create(activity=a,name_az='Fictional OFFER09 group',age_from=6,age_to=12);plan=PricingPlan.objects.create(offering_group=g,product_type='lesson',price='20')
(P/'fixtures.json').write_text(json.dumps({'place':place.pk,'activity':a.pk,'group':g.pk,'plan':plan.pk,'owner_email':owner.email,'admin_username':admin.username},indent=2));print('Own09 fictional grouped-only pricing fixture. No candidate/decision ORM setup.')
