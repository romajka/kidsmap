import ast,hashlib,json,sys
from pathlib import Path
O=Path(__file__).resolve().parent
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site06-pc-plan-r1');sys.argv=['runtime.py','candidate-static'];from runtime import *
from django.template import Engine
from django.template.loader import get_template
from django.test.utils import get_runner
import PIL
assert len(entry['sources'])==1029 and settings.DATABASES['default']['TEST']['NAME']=='test_m10s06_plan_r1_static'
assert settings.CACHES['default']['LOCATION']=='m10s06-plan-r1' and settings.EMAIL_BACKEND=='django.core.mail.backends.locmem.EmailBackend'
assert str(settings.MEDIA_ROOT)==str(QA/'media') and str(settings.PRIVATE_MEDIA_ROOT)==str(QA/'private-media')
assert not any([settings.GOOGLE_APPLICATION_CREDENTIALS,settings.GOOGLE_MAPS_API_KEY,settings.GOOGLE_ANALYTICS_PROPERTY_ID,settings.LOCAL_ANALYTICS_STORAGE_ENABLED,settings.OWNER_ANALYTICS_ENABLED])
C=O/'candidate'
for p in C.rglob('*.py'):compile(ast.parse(p.read_text()),str(p),'exec')
Engine.get_default().from_string((C/'src/catalog/templates/admin/catalog/shared_settings_change_form.html').read_text())
assert str(get_template('admin/catalog/shared_settings_change_form.html').origin.name)==str(ROOT/'src/catalog/templates/admin/catalog/shared_settings_change_form.html')
labels=['test_site06_candidate','catalog.testcases.test_site_qa01_media_permissions','catalog.testcases.test_site_qa15_settings_concurrency','catalog.testcases.admin.TestSiteGalleryImageAdminMedia','catalog.testcases.admin.TestAdminSidebarStructure','catalog.testcases.test_public_section_switches']
suite=get_runner(settings)(verbosity=0).build_suite(labels)
def ids(s):
 for x in s:
  if hasattr(x,'id'):yield x.id()
  else:yield from ids(x)
methods=list(ids(suite));assert len(methods)==len(set(methods))==84
result={'candidate_AST_compile':True,'candidate_template_compiles':True,'current_template_origin':str(get_template('admin/catalog/shared_settings_change_form.html').origin.name),'actual_runtime':{'python':sys.version.split()[0],'django':django.get_version(),'Pillow':PIL.__version__},'isolated_profile':True,'current_root_locales_verified':manifest,'test_methods':methods,'candidate_execution':'NOT RUN; no candidate Python module imported/executed, template compile only','source1029_verified':True}
(QA/'static-result.json').write_text(json.dumps(result,indent=2));print(json.dumps({'static_python_template':True,'current_source1029':True,'test_methods':84,'candidate_green':'NOT RUN'}))
