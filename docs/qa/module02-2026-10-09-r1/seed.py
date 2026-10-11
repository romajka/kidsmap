import secrets,json,hashlib
from io import BytesIO
from decimal import Decimal
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from catalog.models import Place,PlacePhoto,Activity,OfferingGroup,PricingPlan
from catalog.testcases.utils import create_ready_place,ensure_quality_subcategory
assert not Place.objects.exists()
credential=secrets.token_hex(16)
(STATE/'credential').write_text(credential)
actors={}
for role in ['owner','outsider','employee','direct','newowner','moderator','employee2']:
    u,_=get_user_model().objects.get_or_create(username='qa_'+role,defaults={'email':role+'@example.invalid'})
    u.set_password(credential);u.save(update_fields=['password'])
    if role=='moderator':u.is_staff=u.is_superuser=True;u.save(update_fields=['is_staff','is_superuser'])
    actors[role]=u
subcategory=ensure_quality_subcategory('EDU')
for i in range(1,33):
    owner=actors['outsider'] if i in [21,22,23,24,25,27,28,29,30] else actors['owner']
    name=f'QA02 BULK {i:02}' if i<=10 else f'QA02 PLACE {i:02}'
    private=i in [25,26]
    p=create_ready_place(owner=owner,created_by=owner,name=name,name_az=name,name_ru=name+' RU',name_en=name+' EN',address=f'QA02 fictional address {i:02}',district='baku_yasamal',schedule_mode='regular',subcategory=subcategory,status='draft' if private else 'published',is_active=not private,lat=None,lng=None)
    for n,color in enumerate(['#81b8a2','#dbb876','#a5bfe5']):
        b=BytesIO();Image.new('RGB',(1000,750),color).save(b,format='PNG');content=ContentFile(b.getvalue())
        if n==0:p.photo.save(f'qa02-cover-{i}.png',content,save=True)
        else:
            photo=PlacePhoto(place=p,order=n-1,caption=f'QA02 synthetic {n}');photo.image.save(f'qa02-gallery-{i}-{n}.png',content,save=True)
    a=Activity.objects.create(place=p,name_az=f'QA02 dərs {i}',status='published')
    g=OfferingGroup.objects.create(activity=a,name_az=f'QA02 qrup {i}',age_from=6,age_to=12,schedule_text='Saturday 14:00–15:00',lesson_format='group')
    PricingPlan.objects.create(offering_group=g,product_type='lesson',charge_role='primary',price_kind='exact',price=Decimal('20'),title_az='QA02 lesson ticket')
ids={'actors':{r:u.pk for r,u in actors.items()},'bulk':list(range(1,11)),'places':list(range(1,33)),'private_foreign':25,'private_own':26,'outsider_public':21,'common_program_branch':11,'other_network_branch':12,'race_branch':13,'transfer_branch':14,'legacy_detach_branch':15,'informational':[27,28,29,30]}
(HERE/'fixture-ids.json').write_text(json.dumps(ids,indent=2),encoding='utf-8')
print('Synthetic actors7; standalone places32; photos96; activities32/groups32. No organization links assigned.')
