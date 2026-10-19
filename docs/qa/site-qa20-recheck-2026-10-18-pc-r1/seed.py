import sys,json
from pathlib import Path
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q));sys.argv=['runtime.py','seed-own'];from runtime import *
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from catalog.models import CatalogContentSettings,SiteSettings
assert get_user_model().objects.count()==0
sys.path.insert(0,str(ROOT/'docs/qa/site-qa20-recheck-2026-10-18-pc-r1'))
from test_site19_candidate import INITIAL
obj=CatalogContentSettings.get_solo()
for k,v in INITIAL.items():setattr(obj,k,v)
obj.save();assert obj.pk==1
SiteSettings.get_solo()
for role in ['super','editor','viewer','denied']:
 user=get_user_model().objects.create_user('site08_'+role,'site08_'+role+'@example.invalid','fictional',is_staff=True,is_superuser=role=='super')
 if role in ['editor','viewer']:
  codes=['view_catalogcontentsettings']+(['change_catalogcontentsettings'] if role=='editor' else [])
  perms=Permission.objects.filter(content_type__app_label='catalog',codename__in=codes);assert perms.count()==len(codes);user.user_permissions.add(*perms)
print(json.dumps({'synthetic_users':4,'content_pk':obj.pk,'model_source_guard':True,'production_data':False}))

from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
site=SiteSettings.get_solo();bio=BytesIO();Image.new('RGB',(32,32),'#0d8a52').save(bio,format='PNG')
site.logo.save('synthetic_'+('long_filename_'*8)+'.png',ContentFile(bio.getvalue()),save=False)
site.brand_name='KidsMap QA synthetic';site.footer_email='qa@example.invalid'
for lang in ['ru','az','en']:setattr(site,'about_text_'+lang,'QA '+lang+' synthetic paragraph. '*10)
site.save()
print('Own synthetic settings fixture populated; local media only.')

from pathlib import Path
assets=QA/'assets';assets.mkdir(exist_ok=True)
for n,size,color in [('valid_'+('long_name_'*8)+'.png',128,'#0d8a52'),('restore.png',32,'#0d8a52')]:
 Image.new('RGB',(size,size),color).save(assets/n,format='PNG')
(assets/'broken.png').write_bytes(b'not-a-png')

for role,codename in [('section_editor','change_sitefootersettings'),('section_viewer','view_sitefootersettings')]:
 user=get_user_model().objects.create_user('site08_'+role,'site08_'+role+'@example.invalid','fictional',is_staff=True)
 user.user_permissions.add(Permission.objects.get(content_type__app_label='catalog',codename=codename))
 assert not user.has_perm('catalog.view_sitesettings') and not user.has_perm('catalog.change_sitesettings')
print('Own two section-only actors seeded; no SiteSettings grant.')

from catalog.models import SiteGalleryImage
models=('sitebrandingsettings','siteaboutsettings','sitecontactssettings','sitefootersettings','siteemptystatesettings','sitevisibilitysettings','siteanalytics','catalogcontentsettings','sitegalleryimage')
for role,codes in [('all_viewer',['view_'+m for m in models]),('all_editor',['change_'+m for m in models]),('gallery_adder',['add_sitegalleryimage']),('gallery_deleter',['view_sitegalleryimage','delete_sitegalleryimage'])]:
 user=get_user_model().objects.create_user('site08_'+role,role+'@example.invalid','fictional',is_staff=True)
 perms=Permission.objects.filter(content_type__app_label='catalog',codename__in=codes);assert perms.count()==len(codes);user.user_permissions.add(*perms)
SiteGalleryImage.objects.create(image=site.logo.name,title_ru='SITE20 synthetic gallery')
print('Four scoped actors and one synthetic gallery row added.')
