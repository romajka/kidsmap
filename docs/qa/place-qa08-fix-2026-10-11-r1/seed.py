"""Initial synthetic published fixture; all subsequent saves use native UI."""
import json
import sys
sys.argv=['run.py','qa-seed']
from run import *
from django.contrib.auth import get_user_model
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone, translation
from catalog.models import Place, UserEmailVerification, SiteSettings
from catalog.testcases.utils import create_ready_place
from PIL import Image, ImageDraw

U=get_user_model()
assert U.objects.count()==0 and Place.objects.count()==0
credential=(STATE/'credential').read_text(encoding='utf-8')
owner=U.objects.create_user('qa08_owner',email='owner08@example.invalid',password=credential,first_name='Fictional QA08')
UserEmailVerification.objects.update_or_create(user=owner,defaults={'email':owner.email,'is_verified':True,'verified_at':timezone.now()})
image=Image.new('RGB',(800,600),'#CDE7C5')
ImageDraw.Draw(image).text((30,30),'FICTIONAL QA08 DISTRICT FIXTURE',fill='#136F38')
photo=STATE/'media/places/qa08.png'
photo.parent.mkdir(parents=True,exist_ok=True)
image.save(photo)
place=create_ready_place(owner=owner,created_by=owner,name='Fictional QA08 district fixture',name_az='Uydurma QA08 rayon mekani',name_ru='Вымышленное QA08 место района',name_en='Fictional QA08 district fixture',district='baku_yasamal',address='Fictional QA08 address 08',lat=None,lng=None,photo='places/qa08.png',status='published')
urls={}
for lang in ('ru','az','en'):
    with translation.override(lang): urls[lang]=place.get_absolute_url()
site=SiteSettings.objects.first() or SiteSettings()
site.brand_name='Fictional QA08'
site.footer_email='support08@example.invalid'
site.save()
fixtures={'actors':{'owner':{'id':owner.pk,'email':owner.email,'username':owner.username}},'place':place.pk,'public_urls':urls,'initial_seed_only':True,'synthetic_only':True}
(HERE/'fixtures.json').write_text(json.dumps(fixtures,ensure_ascii=False,indent=2),encoding='utf-8')
isolation={'testing':settings.TESTING,'db_name':'qa08_district','db_port':55447,'cache_backend':settings.CACHES['default']['BACKEND'],'email_backend':settings.EMAIL_BACKEND,'media':str(settings.MEDIA_ROOT),'private_media':str(settings.PRIVATE_MEDIA_ROOT),'locale_paths':list(settings.LOCALE_PATHS),'manifest_verified_before_django_setup':True,'migrations':MigrationRecorder.Migration.objects.count(),'external_network_blocked':True,'external_credentials_configured':False,'synthetic_only':True}
(HERE/'isolation.json').write_text(json.dumps(isolation,indent=2),encoding='utf-8')
print('Initial synthetic owner and published Place created; no audited UI transition seeded')
