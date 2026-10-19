import ast,hashlib,json,sys
from pathlib import Path
O=Path(__file__).resolve().parent
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site15-pc-fix-r1');sys.argv=['runtime.py','static-verification'];from runtime import *
from django.template.loader import get_template
from django.test.utils import get_runner
from django.utils import translation
from catalog.models import CatalogContentSettings
from django.db import connection,transaction
for p in ['src/catalog/domain_admin/site.py','src/catalog/testcases/test_site_qa15_settings_concurrency.py']:ast.parse((ROOT/p).read_text())
t=get_template('admin/catalog/shared_settings_change_form.html');assert str(t.origin.name)==str(ROOT/'src/catalog/templates/admin/catalog/shared_settings_change_form.html')
labels=['catalog.testcases.test_site_qa15_settings_concurrency','catalog.testcases.test_site_qa01_media_permissions','catalog.testcases.admin.TestSiteGalleryImageAdminMedia','catalog.testcases.admin.TestAdminSidebarStructure','catalog.testcases.test_public_section_switches']
suite=get_runner(settings)(verbosity=0).build_suite(labels)
def ids(s):
 for x in s:
  if hasattr(x,'id'):yield x.id()
  else:yield from ids(x)
methods=list(ids(suite));assert len(methods)==55 and len(set(methods))==55
msg='Настройки изменились в другой вкладке. Ваш ввод не сохранён. Скопируйте нужные значения и откройте текущую версию отдельно.'
localized={}
for lang in ['ru','az','en']:
 with translation.override(lang):localized[lang]=translation.gettext(msg)
assert len(set(localized.values()))==3
safe={'testing':settings.TESTING,'source1029_guard':len(entry['sources'])==1029,'owned_normal_db':settings.DATABASES['default']['NAME']=='m10s15_fix_r1','owned_test_db':settings.DATABASES['default']['TEST']['NAME']=='test_m10s15_fix_r1_preview','owned_cache':settings.CACHES['default']['LOCATION']=='m10s15-fix-r1','owned_media':str(settings.MEDIA_ROOT)==str(QA/'media'),'owned_private_media':str(settings.PRIVATE_MEDIA_ROOT)==str(QA/'private-media'),'locmem_email':settings.EMAIL_BACKEND=='django.core.mail.backends.locmem.EmailBackend','sole_current_locale':list(map(str,settings.LOCALE_PATHS))==[manifest['locale_root']],'external_disabled':not any([settings.GOOGLE_APPLICATION_CREDENTIALS,settings.GOOGLE_MAPS_API_KEY,settings.GOOGLE_ANALYTICS_PROPERTY_ID,settings.GOOGLE_OAUTH_CLIENT_SECRET,settings.LOCAL_ANALYTICS_STORAGE_ENABLED,settings.OWNER_ANALYTICS_ENABLED]),'clean_env':set(os.environ)<=set(['DJANGO_TESTING','DJANGO_SETTINGS_MODULE','PYTHONDONTWRITEBYTECODE','PATH','HOME','LANG','TMPDIR','TZ'])}
assert all(safe.values()),safe
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");catalog_exists=CatalogContentSettings.objects.filter(pk=1).exists()
result={'safe':safe,'python_ast':True,'template_origin':str(t.origin.name),'test_methods':methods,'localized':localized,'locale_manifest':manifest,'catalog_fixture_exists':catalog_exists}
(QA/'static-runtime.json').write_text(json.dumps(result,indent=2));print(json.dumps({'all_safety_checks':True,'template_compiled':True,'test_methods':len(methods),'catalog_fixture_exists':catalog_exists}))
