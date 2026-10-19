import sys,json
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site15-pc-plan-r1');sys.argv=['runtime.py','plan-fixtures'];from runtime import *
from django.contrib.auth import get_user_model
from catalog.models import SiteSettings
from catalog.services.staff_roles import ADMIN_ROLE_CONTENT_MANAGER,role_permissions
U=get_user_model();assert not U.objects.exists()
for name in ['content','super']:
 u=U.objects.create_user(username='site15_'+name,email='site15-'+name+'@example.invalid',is_staff=True,is_superuser=name=='super')
 if name=='content':u.user_permissions.set(role_permissions(ADMIN_ROLE_CONTENT_MANAGER))
s=SiteSettings.get_solo();s.footer_phone='+994500001500';s.footer_email='site15-initial@example.invalid';s.save()
print(json.dumps({'fictional_roles':2,'normal_db':'m10s15_plan_r1','settings_pk':s.pk}))
