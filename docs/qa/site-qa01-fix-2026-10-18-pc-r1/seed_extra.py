import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site01-pc-fix-r1')
sys.argv=['runtime.py','extra-fixtures'];from runtime import *
from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from catalog.models import SiteSettings,SiteGalleryImage
from catalog.models.site import clear_singleton_caches
import io
b=io.BytesIO();Image.new('RGB',(80,40),'green').save(b,'PNG');data=b.getvalue();(QA/'fixture.png').write_bytes(data)
site=SiteSettings.get_solo();site.logo=SimpleUploadedFile('baseline-logo.png',data,content_type='image/png');site.save();clear_singleton_caches()
SiteGalleryImage.objects.create(image=SimpleUploadedFile('baseline-gallery.png',data,content_type='image/png'),placement=SiteGalleryImage.PLACEMENT_HOME_HERO,title_ru='QA gallery')
U=get_user_model()
for role,perms,flags in [('addviewer',['view_sitegalleryimage','add_sitegalleryimage'],{}),('nonstaff',['change_sitesettings'],{'is_staff':False}),('inactive',['change_sitesettings'],{'is_active':False}),('proxyonly',['change_sitebrandingsettings'],{})]:
    u=U.objects.create_user(username='site01_'+role,email='site01-'+role+'@example.invalid',is_staff=flags.get('is_staff',True),is_active=flags.get('is_active',True));u.user_permissions.set(Permission.objects.filter(content_type__app_label='catalog',codename__in=perms))
print(json.dumps({'fictional_extra_roles':4,'logo':bool(site.logo),'gallery':SiteGalleryImage.objects.count(),'all_migrations_applied':True}))
