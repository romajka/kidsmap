import sys,json
sys.argv=['run.py','qa-source-check'];from run import *
from django.contrib.auth import get_user_model
from django.db import transaction,connection
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 u=get_user_model().objects.get(username='qa10_staff')
 x={'fixture':'qa10_staff','is_staff':u.is_staff,'is_superuser':u.is_superuser,'user_permission_count':u.user_permissions.count(),'group_count':u.groups.count(),'can_change_site_settings':u.has_perm('catalog.change_sitesettings'),'can_change_gallery':u.has_perm('catalog.change_sitegalleryimage')}
(HERE/'acl-identity.json').write_text(json.dumps(x,indent=2))
print(json.dumps(x))
