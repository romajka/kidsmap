"""Initial synthetic catalog only. Later audited mutations use native admin UI."""
import sys,json
sys.stdout.reconfigure(encoding='utf-8')
sys.argv=['run.py','qa-bootstrap']
from run import *
from django.contrib.auth import get_user_model
from django.utils import timezone,translation
from django.core.files.base import ContentFile
from django.db.migrations.recorder import MigrationRecorder
from catalog.models import Place,PlacePhoto,Category,Subcategory,Organization,Activity,OfferingGroup,PricingPlan,Location,Specialist,Event,SiteSettings
from catalog.testcases.utils import create_quality_place,ensure_quality_subcategory
from catalog.services.catalog_structure import bind_confirmed_location
from catalog.services import organization_ownership
from PIL import Image,ImageDraw
from io import BytesIO
from datetime import timedelta
assert not (HERE/'fixtures.json').exists(), 'Never reset an audited stand'
assert set(get_user_model().objects.values_list('username',flat=True)) <= {'qa_admin','qa_owner'}
call_command('flush',interactive=False,verbosity=0)  # Own disposable DB, failed initial setup only.
from io import StringIO
call_command('seed_catalog_taxonomy',verbosity=0,stdout=StringIO())
password=(STATE/'credential').read_text()
admin=get_user_model().objects.create_superuser('qa_admin','admin@example.invalid',password)
owner=get_user_model().objects.create_user('qa_owner',email='owner@example.invalid',password=password)
out=BytesIO();im=Image.new('RGB',(900,600),'#cde7c5');ImageDraw.Draw(im).text((60,80),'FICTIONAL QA06 - LOCAL ONLY',fill='#136f38');im.save(out,format='PNG');img=out.getvalue()
org=Organization.objects.create(name_az='Uydurma Aurora şəbəkəsi',name_ru='Вымышленная сеть Аврора',name_en='Fictional Aurora network',description_az='Uydurma test təşkilatı. '*20,description_ru='Вымышленная сеть. '*20,description_en='Fictional network. '*20,status='published',approved_at=timezone.now(),owner=owner,phone='+994500000006')
places={};categories={code:Category.objects.get(pk=code) for code in ('EDU','ART','SPRT')}
subs={k:ensure_quality_subcategory(c) for k,c in categories.items()}
def place(key,**kw):
 base=dict(name='Uydurma '+key,name_az='Uydurma '+key,name_ru='Вымышленное '+key,name_en='Fictional '+key,description_az='Uydurma yer və valideynlər üçün məlumat. '*12,description_ru='Вымышленная площадка с занятиями и семейными встречами. '*12,description_en='Fictional family venue with lessons and meetings. '*12,category=categories['EDU'],subcategory=subs['EDU'],owner=owner,created_by=owner,address='Uydurma küçə 06 '+key,district='baku_yasamal',city='baku',phone1='+994500000006',schedule_mode='always_open',price_mode='free',age_from=3,age_to=17,lat=40.41,lng=49.87)
 base.update(kw);p=create_quality_place(**base);p.photo.save('qa06-'+key+'.png',ContentFile(img),save=True);places[key]=p;return p
mixed=place('Aurora',name_az='Uydurma Aurora dərsləri',name_ru='Вымышленные занятия Аврора',name_en='Fictional Aurora lessons',price_mode='tariffs')
groups={}
for key,code,lo,hi,price in [('Younger','EDU',4,6,'25'),('Older','ART',9,13,'120'),('Sports','SPRT',7,10,'40')]:
 a=Activity.objects.create(place=mixed,status='published',category=categories[code],subcategory=subs[code],name_az='Uydurma '+key,name_ru={'Younger':'Вымышленный английский','Older':'Вымышленное рисование','Sports':'Вымышленный спорт'}[key],name_en='Fictional '+key,description_az='Uydurma məlumat. '*20)
 g=OfferingGroup.objects.create(activity=a,name_az=key,name_ru=key,name_en=key,age_from=lo,age_to=hi,schedule_text='Tue 16:00–17:00',lesson_format='group')
 PricingPlan.objects.create(offering_group=g,product_type='lesson',price=price,currency='AZN',quantity=1,quantity_unit='lesson');groups[key]={'activity':a.pk,'group':g.pk}
secret=Activity.objects.create(place=mixed,status='draft',category=categories['ART'],name_az='HIDDEN06_PRIVATE_ACTIVITY')
g=OfferingGroup.objects.create(activity=secret,name_az='HIDDEN06_PRIVATE_GROUP',age_from=4,age_to=6)
PricingPlan.objects.create(offering_group=g,product_type='lesson',price='999',currency='AZN',quantity=1,quantity_unit='lesson')
peer=place('VenuePeer',category=categories['SPRT'],subcategory=subs['SPRT'],district='baku_narimanov')
venue=Location.objects.create(address='Uydurma shared venue 06',lat=40.42,lng=49.88,confirmed_at=timezone.now())
for p in (mixed,peer):bind_confirmed_location(p.pk,venue.pk,expected_content_version=p.content_version);p.refresh_from_db()
place('SameCoordinateA',lat=40.43,lng=49.89)
place('SameCoordinateB',lat=40.43,lng=49.89)
place('NoPoint',lat=None,lng=None,name_ru='Вымышленное место без точки')
z=place('ZeroPoint',lat=None,lng=None);Place.objects.filter(pk=z.pk).update(lat=0,lng=0);z.refresh_from_db()
z=place('PartialPoint',lat=None,lng=None);Place.objects.filter(pk=z.pk).update(lat=40.4,lng=None);z.refresh_from_db()
long=place('LongFallback',name_az='Uydurma uzun adlı ailə və yaradıcılıq mərkəzi '+('Aurora '*20),name_ru='',name_en='',address='Uydurma uzun ünvan '+('Test küçəsi '*12),website='https://example.invalid/qa06',instagram='https://example.invalid/qa06-social')
for i,color in enumerate(('#91bdd1','#ebb889')):
 o=BytesIO();Image.new('RGB',(800,600),color).save(o,format='PNG');photo=PlacePhoto(place=long,order=i,caption='Fictional gallery '+str(i));photo.image.save('qa06-gallery-'+str(i)+'.png',ContentFile(o.getvalue()),save=True)
for i in range(17):place('Page'+str(i).zfill(2),district='baku_narimanov' if i%2 else 'baku_yasamal',category=categories['ART'] if i%2 else categories['EDU'],subcategory=subs['ART'] if i%2 else subs['EDU'],lat=40.40+i*.001,lng=49.86+i*.001)
private=[]
for status in ('draft','pending','rejected','inactive','archived'):
 p=place('HIDDEN06_'+status,status=status if status in ('draft','pending','rejected') else 'published',is_active=status!='inactive',deleted_at=timezone.now() if status=='archived' else None);private.append(p.pk)
 Organization.objects.create(name_az='HIDDEN06_ORG_'+status,owner=owner,status=status if status in ('draft','pending','rejected') else 'published',approved_at=timezone.now() if status in ('inactive','archived') else None,archived_at=timezone.now() if status in ('inactive','archived') else None)
spec=Specialist.objects.create(name='Fictional QA06 Specialist',name_alt='Uydurma mütəxəssis',bio_az='Uydurma mütəxəssis. '*20,bio_ru='Вымышленный специалист. '*20,bio_en='Fictional specialist. '*20,status='published',owner=owner,created_by=owner,age_from=4,age_to=14,phone='+994500000006',language_ru=True,consultation_format='online',price_from=60,price_to=80)
spec.photo.save('qa06-specialist.png',ContentFile(img),save=True)
for status in ('draft','pending','rejected','inactive'):Specialist.objects.create(name='HIDDEN06_SPEC_'+status,status=status if status!='inactive' else 'published',is_active=status!='inactive')
events={}
for key,state,offset in [('Scheduled','scheduled',2),('Cancelled','cancelled',3),('Past','scheduled',-3)]:
 e=Event.objects.create(name='Fictional QA06 '+key,name_az='Uydurma '+key,name_ru='Вымышленное '+key,name_en='Fictional '+key,description_az='Uydurma tədbir. '*20,description_ru='Вымышленное мероприятие. '*20,description_en='Fictional event. '*20,category=categories['ART'],organizer_organization=org,related_place=mixed,start_datetime=timezone.now()+timedelta(days=offset),end_datetime=timezone.now()+timedelta(days=offset,hours=2),address='Uydurma küçə 06',event_format='physical',status='published',occurrence_state=state,age_from=3,age_to=16,price_text='Free',phone='+994500000006');e.photo.save('qa06-'+key+'.png',ContentFile(img),save=True);events[key]=e
for status in ('draft','pending','rejected','deleted'):Event.objects.create(name='HIDDEN06_EVENT_'+status,name_az='HIDDEN06_EVENT_'+status,category=categories['ART'],start_datetime=timezone.now()+timedelta(days=3),status=status if status!='deleted' else 'published',deleted_at=timezone.now() if status=='deleted' else None)
site=SiteSettings.get_solo();site.organizations_section_enabled=site.specialists_section_enabled=site.events_section_enabled=True;site.save()
urls={}
for lang in ('ru','az','en'):
 with translation.override(lang):urls[lang]={'places':{k:p.get_absolute_url() for k,p in places.items()},'specialist':spec.get_absolute_url(),'events':{k:e.get_absolute_url() for k,e in events.items()},'organization':f'/{"" if lang=="az" else lang+"/"}organizations/{org.public_id}/'}
(HERE/'fixtures.json').write_text(json.dumps({'synthetic':True,'places':{k:p.pk for k,p in places.items()},'private_places':private,'groups':groups,'organization':org.pk,'specialist':spec.pk,'events':{k:e.pk for k,e in events.items()},'site':site.pk,'urls':urls,'subcategories':{k:v.pk for k,v in subs.items()}},indent=2),encoding='utf-8')
(HERE/'isolation.json').write_text(json.dumps({'python':sys.version.split()[0],'django':django.get_version(),'testing':settings.TESTING,'db':settings.DATABASES['default']['NAME'],'db_port':settings.DATABASES['default']['PORT'],'cache':settings.CACHES['default']['BACKEND'],'email':settings.EMAIL_BACKEND,'media':str(settings.MEDIA_ROOT),'private_media':str(settings.PRIVATE_MEDIA_ROOT),'migrations':MigrationRecorder.Migration.objects.count(),'map_key_present':bool(settings.GOOGLE_MAPS_API_KEY)},indent=2),encoding='utf-8')
print('Synthetic fixture setup complete:',len(places),'places. Password stays ignored.')
