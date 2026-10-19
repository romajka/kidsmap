import ast,hashlib,json,re,sys
from pathlib import Path
O=Path(__file__).resolve().parent
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site06-pc-fix-r1');sys.argv=['runtime.py','applied-static'];from runtime import *
from django.template import Engine
from django.template.loader import get_template
from django.test.utils import get_runner
import PIL
assert len(entry['sources'])==1031 and settings.DATABASES['default']['TEST']['NAME']=='test_m10s06_fix_r1_final'
assert settings.CACHES['default']['LOCATION']=='m10s06-fix-r1' and settings.EMAIL_BACKEND=='django.core.mail.backends.locmem.EmailBackend'
assert str(settings.MEDIA_ROOT)==str(Path('/tmp/site06-pc-fix-r1-media')) and str(settings.PRIVATE_MEDIA_ROOT)==str(QA/'private-media')
assert not any([settings.GOOGLE_APPLICATION_CREDENTIALS,settings.GOOGLE_MAPS_API_KEY,settings.GOOGLE_ANALYTICS_PROPERTY_ID,settings.LOCAL_ANALYTICS_STORAGE_ENABLED,settings.OWNER_ANALYTICS_ENABLED])
paths=['src/catalog/domain_admin/site.py','src/catalog/services/site_media_validation.py','src/catalog/testcases/test_site_qa06_media_validation.py']
for rel in paths:compile(ast.parse((ROOT/rel).read_text()),rel,'exec')
template=ROOT/'src/catalog/templates/admin/catalog/shared_settings_change_form.html';old=O/'entry-source/src/catalog/templates/admin/catalog/shared_settings_change_form.html'
Engine.get_default().from_string(template.read_text());assert str(get_template('admin/catalog/shared_settings_change_form.html').origin.name)==str(template)
pattern=r'{% blocktranslate count counter=errors\|length %}.*?{% endblocktranslate %}'
assert re.findall(pattern,old.read_text(),re.S)==re.findall(pattern,template.read_text(),re.S)
labels=['catalog.testcases.test_site_qa06_media_validation','catalog.testcases.test_site_qa01_media_permissions','catalog.testcases.test_site_qa15_settings_concurrency','catalog.testcases.admin.TestSiteGalleryImageAdminMedia','catalog.testcases.admin.TestAdminSidebarStructure','catalog.testcases.test_public_section_switches']
suite=get_runner(settings)(verbosity=0).build_suite(labels)
def ids(s):
 for x in s:
  if hasattr(x,'id'):yield x.id()
  else:yield from ids(x)
methods=list(ids(suite));assert len(methods)==len(set(methods))==85
result={'AST_compile':paths,'template_compiles':True,'literal_plural_preserved':True,'current_template_origin':str(template),'actual_runtime':{'python':sys.version.split()[0],'django':django.get_version(),'Pillow':PIL.__version__},'isolated_profile':True,'current_root_locales_verified':manifest,'test_methods':methods,'source1031_verified':True}
(QA/'final-static-result.json').write_text(json.dumps(result,indent=2));print(json.dumps({'static_python_template':True,'source1031':True,'test_methods':85,'runtime':result['actual_runtime']}))
