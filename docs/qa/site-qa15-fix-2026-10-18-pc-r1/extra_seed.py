import io,json,sys
from pathlib import Path
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site15-pc-fix-r1');sys.argv=['runtime.py','extra-fixtures'];from runtime import *
from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission,Group
from catalog.services.staff_roles import VOLUNTEER_GROUP
U=get_user_model()
for name,perms in [('proxyfooter',['view_sitefootersettings','change_sitefootersettings']),('viewer',['view_sitefootersettings']),('denied',[]),('volunteer',['view_sitefootersettings','change_sitefootersettings','change_sitesettings','view_sitegalleryimage','add_sitegalleryimage'])]:
 u=U.objects.create_user(username='site15_'+name,email='site15-'+name+'@example.invalid',is_staff=True)
 u.user_permissions.set(Permission.objects.filter(content_type__app_label='catalog',codename__in=perms))
 if name=='volunteer':u.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
b=io.BytesIO();Image.new('RGB',(80,40),'green').save(b,'PNG');(QA/'fixture.png').write_bytes(b.getvalue())
print(json.dumps({'extra_fictional_roles':4,'fixture_png':True,'normal_db_owned':settings.DATABASES['default']['NAME']=='m10s15_fix_r1'}))
