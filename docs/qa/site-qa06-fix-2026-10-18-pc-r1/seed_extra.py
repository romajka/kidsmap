import json,sys
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site06-pc-fix-r1');sys.argv=['runtime.py','extra-fixtures'];from runtime import *
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission,Group
from catalog.services.staff_roles import VOLUNTEER_GROUP
assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s06_fix_r1'
for name,perms in [('proxyfooter',['view_sitefootersettings','change_sitefootersettings']),('viewer',['view_sitefootersettings','view_sitegalleryimage']),('addonly',['view_sitegalleryimage','add_sitegalleryimage']),('denied',[]),('volunteer',['view_sitefootersettings','change_sitefootersettings','change_sitesettings','view_sitegalleryimage','add_sitegalleryimage'])]:
 u=get_user_model().objects.create_user(username='site06_'+name,email='site06-'+name+'@example.invalid',is_staff=True)
 u.user_permissions.set(Permission.objects.filter(content_type__app_label='catalog',codename__in=perms))
 if name=='volunteer':u.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
raw=(QA/'valid.png').read_bytes();(QA/'exact.png').write_bytes(raw.ljust(512000,b' '));(QA/'over.png').write_bytes(raw.ljust(512001,b' '))
print(json.dumps({'extra_fictional_roles':5,'owned_fixture_files':2,'owned_normal_db':True}))
