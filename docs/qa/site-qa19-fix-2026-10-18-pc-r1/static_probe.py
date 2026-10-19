import ast,hashlib,inspect,json,sys
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/site19-pc-fix-r1';O=Path(__file__).resolve().parent
sys.path.insert(0,str(Q));sys.argv=['runtime.py','static-probe'];from runtime import *
from django.conf import settings
from django.utils.translation import gettext,override
from django.db import connection,transaction
from django.test.utils import CaptureQueriesContext
from django.template.loader import get_template
from django.middleware.locale import LocaleMiddleware
from catalog.models import CatalogContentSettings
from django.contrib import admin
from django.test.runner import DiscoverRunner
before=(O/'entry-source/src/catalog/models/site.py').read_bytes();after=(R/'src/catalog/models/site.py').read_bytes()
old=ast.parse(before.decode());new=ast.parse(after.decode())
oc=next(n for n in old.body if isinstance(n,ast.ClassDef) and n.name=='CatalogContentSettings');nc=next(n for n in new.body if isinstance(n,ast.ClassDef) and n.name=='CatalogContentSettings')
om=next(n for n in oc.body if isinstance(n,ast.FunctionDef) and n.name=='__str__');nm=next(n for n in nc.body if isinstance(n,ast.FunctionDef) and n.name=='__str__');om.body=nm.body;assert ast.dump(old)==ast.dump(new)
labels={};types={}
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
 obj=CatalogContentSettings.objects.get(pk=1)
 for lang in ['az','ru','en']:
  with override(lang),CaptureQueriesContext(connection) as queries:
   value=str(obj);assert type(value) is str and value==gettext('Контент каталога');labels[lang]=value;types[lang]=type(value).__name__
  assert len(queries)==0
assert str(settings.MEDIA_ROOT)=='/tmp/site19-pc-fix-r1-media' and str(settings.PRIVATE_MEDIA_ROOT)==str(Q/'private-media')
assert settings.CACHES['default']['BACKEND'].endswith('LocMemCache') and settings.EMAIL_BACKEND.endswith('locmem.EmailBackend')
assert not settings.INDEXNOW_KEY and not settings.GOOGLE_OAUTH_CLIENT_SECRET and not settings.GOOGLE_MAPS_API_KEY and not settings.SOCIALACCOUNT_PROVIDERS
labels_test=['catalog.testcases.test_site_qa19_catalog_content','catalog.testcases.public.TestCatalogContentSettingsWiring','catalog.testcases.test_site_qa06_media_validation','catalog.testcases.test_site_qa01_media_permissions','catalog.testcases.test_site_qa15_settings_concurrency','catalog.testcases.admin.TestSiteGalleryImageAdminMedia','catalog.testcases.admin.TestAdminSidebarStructure','catalog.testcases.test_public_section_switches']
suite=DiscoverRunner(verbosity=0).build_suite(labels_test)
def flatten(s):
 for x in s:
  if hasattr(x,'id'):yield x.id()
  else:yield from flatten(x)
ids=list(flatten(suite));assert len(ids)==len(set(ids))==105
result={'source_count':1032,'existing_AST_delta':'one __str__ return expression; fields/Meta/signals/JSON/admin unchanged','root_current_PO_labels':labels,'model_return_types':types,'queries_in_each_str':0,'unsaved_translation_queries':0,'python_version':sys.version.split()[0],'django_version':__import__('django').get_version(),'template_origin':str(get_template('admin/catalog/shared_settings_change_form.html').origin),'fieldset_origin':str(get_template('admin/includes/fieldset.html').origin),'test_ids':ids,'testing':settings.TESTING,'normal_db':'m10s19_fix_r1','green_test_db':settings.DATABASES['default']['TEST']['NAME'],'media':str(settings.MEDIA_ROOT),'private_media':str(settings.PRIVATE_MEDIA_ROOT),'cache_email':'own locmem','external_integrations_disabled':True,'environment_cleared_before_setup':True,'locale_manifest_verified_before_setup':True,'installed_locale_request_source':inspect.getsource(LocaleMiddleware.process_request)}
(Q/'static-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'source_count':1032,'labels':labels,'test_ids':len(ids),'AST_verified':True,'isolation_verified':True},ensure_ascii=False))
