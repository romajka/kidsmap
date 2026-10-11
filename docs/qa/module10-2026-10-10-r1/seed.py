"""Only initial synthetic fixtures; all audited settings edits use native admin UI."""
import sys,json
sys.argv=['run.py','qa-seed'];from run import *
sys.stdout.reconfigure(encoding='utf-8')
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from django.db.migrations.recorder import MigrationRecorder
from datetime import timedelta
from catalog.models import *
from catalog.testcases.utils import create_ready_place
from PIL import Image,ImageDraw
U=get_user_model();assert U.objects.count() in [0,4]
pw=(STATE/'credential').read_text();actors={}
for role in ['owner','staff','admin','outsider']:
 u=U.objects.filter(username='qa10_'+role).first() or U.objects.create_user('qa10_'+role,email=role+'10@example.invalid',password=pw,first_name='Fictional QA10',last_name=role,is_staff=role in ['staff','admin'],is_superuser=role=='admin')
 UserEmailVerification.objects.update_or_create(user=u,defaults={'email':u.email,'is_verified':True,'verified_at':timezone.now()})
 actors[role]=u
for name,size,color in [('fixture',(800,600),'#136F38'),('logo',(256,256),'#bde6cc'),('hero-pc',(1600,600),'#cceaca'),('hero-mobile',(800,1000),'#dbe8fb'),('replacement',(800,600),'#efdcbd')]:
 image=Image.new('RGB',size,color);ImageDraw.Draw(image).text((20,20),'FICTIONAL QA10 '+name,fill='#111111');image.save(STATE/'assets'/f'{name}.png')
(STATE/'assets/bad.txt').write_text('fictional invalid image input')
media=Path(settings.MEDIA_ROOT)/'places/qa10.png';media.parent.mkdir(parents=True,exist_ok=True);media.write_bytes((STATE/'assets/fixture.png').read_bytes())
places={}
for label,status,active in [('live','published',True),('draft','draft',True),('inactive','published',False),('archived','archived',True),('deleted','published',True)]:
 p=create_ready_place(name='Fictional QA10 '+label,name_az='Uydurma QA10 '+label,name_ru='Вымышленное QA10 '+label,name_en='Fictional QA10 '+label,owner=actors['owner'],created_by=actors['owner'],status=status,is_active=active,photo='places/qa10.png',cover_photo='',description_az='Uydurma məkan. '*30,description_ru='Вымышленное место. '*30,description_en='Fictional place. '*30,deleted_at=timezone.now() if label=='deleted' else None,lat=40.4,lng=49.8)
 places[label]=p.pk
org=Organization.objects.create(owner=actors['owner'],name_az='Uydurma QA10 şəbəkə',name_ru='Вымышленная QA10 сеть',name_en='Fictional QA10 network',status='published',approved_at=timezone.now(),phone='+994000000010')
from catalog.services.organization_ownership import request_join
request_join(actor=actors['owner'],place_id=places['live'],organization_id=org.pk)
spec=Specialist.objects.create(owner=actors['owner'],created_by=actors['owner'],name='Fictional QA10 specialist',name_alt='Uydurma QA10 mütəxəssis',status='published',is_active=True,bio_az='Uydurma mütəxəssis. '*25)
event=Event.objects.create(owner=actors['owner'],name='Fictional QA10 event',name_az='Uydurma QA10 tədbir',category=Place.objects.get(pk=places['live']).category,status='published',event_format='online',start_datetime=timezone.now()+timedelta(days=5),end_datetime=timezone.now()+timedelta(days=5,hours=1),description_az='Uydurma tədbir. '*25)
site=SiteSettings.objects.first() or SiteSettings()
site.brand_name='Fictional QA10';site.footer_email='support10@example.invalid';site.footer_phone='+994000000010';site.footer_whatsapp='https://example.invalid/qa10-chat'
for f in site._meta.fields:
 if f.get_internal_type()=='FileField':setattr(site,f.name,'')
 if f.name.startswith(('home_title_','home_subtitle_','home_search_','home_cta_text_','contacts_text_','about_text_','empty_results_text_')):setattr(site,f.name,'')
for f in ['footer_instagram','footer_telegram','footer_youtube','footer_tiktok','footer_facebook','footer_linkedin']:setattr(site,f,'https://example.invalid/qa10-'+f)
site.save()
for i,g in enumerate(SiteGalleryImage.objects.all()):
 target=Path(settings.MEDIA_ROOT)/f'site/initial-{i}.png';target.parent.mkdir(exist_ok=True);target.write_bytes((STATE/'assets/fixture.png').read_bytes())
 g.image=f'site/initial-{i}.png';g.title_ru=g.title_en=g.title_az=f'Synthetic QA10 initial {i}';g.is_active=False;g.save()
for label in places:PlaceLike.objects.create(place_id=places[label],user=actors['owner'])
from django.urls import reverse
from django.utils.translation import override
urls={}
for lang in ['ru','az','en']:
 with override(lang):
  urls[lang]={'place':Place.objects.get(pk=places['live']).get_absolute_url(),'specialist':spec.get_absolute_url(),'event':event.get_absolute_url(),'organization':reverse('organization_detail',args=[org.public_id])}
(HERE/'fixtures.json').write_text(json.dumps({'actors':{r:{'id':u.pk,'username':u.username,'email':u.email} for r,u in actors.items()},'places':places,'specialist':spec.pk,'event':event.pk,'organization':org.pk,'organization_public_id':str(org.public_id),'urls':urls,'settings':site.pk,'synthetic_only':True},indent=2),encoding='utf-8')
(HERE/'isolation.json').write_text(json.dumps({'python':sys.version.split()[0],'django':django.get_version(),'testing':settings.TESTING,'db':'module10','db_port':'55441','cache':settings.CACHES['default'],'email':settings.EMAIL_BACKEND,'media':str(settings.MEDIA_ROOT),'private_media':str(settings.PRIVATE_MEDIA_ROOT),'migrations':MigrationRecorder.Migration.objects.count(),'external_integrations':False},indent=2))
print('Fresh fictional initial fixtures created')
