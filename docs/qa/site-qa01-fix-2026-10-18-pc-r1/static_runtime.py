import sys,json,ast
from pathlib import Path
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site01-pc-fix-r1');sys.argv=['runtime.py','static-proof'];from runtime import *
from django.template.loader import get_template
from django.test.utils import get_runner
from django.db import connection,transaction
from django.contrib import admin
from catalog.models import SiteGalleryImage
from django.core.cache import caches
from django.core.mail import get_connection
for p in ['src/catalog/domain_admin/site.py','src/catalog/testcases/test_site_qa01_media_permissions.py']:ast.parse((ROOT/p).read_text())
template=get_template('admin/catalog/sitegalleryimage/change_list.html');assert template.origin.name==str(ROOT/'templates/admin/catalog/sitegalleryimage/change_list.html')
suite=get_runner(settings)(verbosity=0,interactive=False).build_suite(['catalog.testcases.test_site_qa01_media_permissions','catalog.testcases.admin.TestSiteGalleryImageAdminMedia','catalog.testcases.admin.TestAdminSidebarStructure'])
def ids(s):
 for t in s:
  if hasattr(t,'id'):yield t.id()
  else:yield from ids(t)
methods=list(ids(suite));assert len(methods)==28
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
  c.execute('select app,name from django_migrations');applied=set(c.fetchall())
 from django.db.migrations.executor import MigrationExecutor
 executor=MigrationExecutor(connection);pending=executor.migration_plan(executor.loader.graph.leaf_nodes());assert not pending
result={'python_ast':True,'template_compile':True,'template_origin':template.origin.name,'methods':methods,'method_count':len(methods),'all_migrations_applied':not pending,
 'scope_checks':{'DJANGO_TESTING':settings.TESTING,'database_owned':settings.DATABASES['default']['NAME']=='m10s01_fix_r1','test_database_owned':settings.DATABASES['default']['TEST']['NAME']=='test_m10s01_fix_r1','cache_local':caches['default'].__class__.__name__=='LocMemCache','email_local':get_connection().__class__.__module__=='django.core.mail.backends.locmem','media_owned':str(settings.MEDIA_ROOT)==str(QA/'media'),'private_media_owned':str(settings.PRIVATE_MEDIA_ROOT)==str(QA/'private-media'),'sole_fresh_locales':list(map(str,settings.LOCALE_PATHS))==[str(QA/'locales/locale')],'external_analytics_off':not settings.LOCAL_ANALYTICS_STORAGE_ENABLED and not settings.OWNER_ANALYTICS_ENABLED,'no_inherited_database_credentials':not os.environ.get('DATABASE_URL'),'sources_match':True}}
assert all(result['scope_checks'].values())
print(json.dumps(result,indent=2))
