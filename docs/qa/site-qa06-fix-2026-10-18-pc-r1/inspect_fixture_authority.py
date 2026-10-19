import json,sys
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site06-pc-fix-r1');sys.argv=['runtime.py','fixture-authority'];from runtime import *
from django.contrib.auth import get_user_model
rows=[]
for role in ['proxyfooter','viewer','addonly','denied','volunteer']:
 u=get_user_model().objects.get(username='site06_'+role);rows.append({'fictional_role':role,'staff':u.is_staff,'active':u.is_active,'superuser':u.is_superuser,'direct_permission_count':u.user_permissions.count(),'footer_view':u.has_perm('catalog.view_sitefootersettings'),'footer_change':u.has_perm('catalog.change_sitefootersettings'),'settings_change':u.has_perm('catalog.change_sitesettings'),'gallery_view':u.has_perm('catalog.view_sitegalleryimage'),'groups_count':u.groups.count()})
(QA/'fixture-authority.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
