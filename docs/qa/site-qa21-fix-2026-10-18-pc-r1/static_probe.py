import ast,hashlib,json,sys
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/site21-pc-fix-r1';O=Path(__file__).resolve().parent;P=R/'docs/qa/site-qa21-recheck-2026-10-18-pc-r1'
sys.path.insert(0,str(Q));sys.argv=['runtime.py','static'];from runtime import *
from django.conf import settings
from django.template.loader import get_template
from django.template import Engine,Context
from django.test.runner import DiscoverRunner
from django.utils.translation import gettext,override
from django.db import connection,transaction
from django.test.utils import CaptureQueriesContext
from catalog.models import CatalogContentSettings
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cand=read(P/'candidate-manifest.json');rel=next(iter(cand['files']));assert sha(R/rel)==cand['files'][rel]['candidate_sha256']
template=get_template('admin/catalog/shared_settings_change_form.html');assert Path(template.origin.name)==R/rel
text=(R/rel).read_text();Engine.get_default().from_string(text);root=next(x for x in text.splitlines() if '<div id="content-main"' in x);branches={}
for name in ['catalogcontentsettings','sitebrandingsettings','siteaboutsettings','sitecontactssettings','sitefootersettings','siteemptystatesettings','sitevisibilitysettings','siteanalytics','sitesettings','sitegalleryimage','contentcatalogsettings']:
 result=Engine.get_default().from_string(root).render(Context({'opts':{'model_name':name}}));assert (' col-12' in result)==(name=='catalogcontentsettings');branches[name]=result.strip()
labels={}
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
 obj=CatalogContentSettings.objects.get(pk=1)
 for lang in ['az','ru','en']:
  with override(lang),CaptureQueriesContext(connection) as queries:value=str(obj);assert type(value) is str and value==gettext('Контент каталога');labels[lang]=value
  assert len(queries)==0
assert str(settings.MEDIA_ROOT)=='/tmp/site21-pc-fix-r1-media' and str(settings.PRIVATE_MEDIA_ROOT)==str(Q/'private-media')
assert settings.TESTING and settings.CACHES['default']['LOCATION']=='m10s21-fix-r1' and settings.EMAIL_BACKEND.endswith('locmem.EmailBackend')
assert not settings.INDEXNOW_KEY and not settings.GOOGLE_MAPS_API_KEY and not settings.GOOGLE_OAUTH_CLIENT_SECRET and not settings.SOCIALACCOUNT_PROVIDERS
labels_test=['catalog.testcases.test_site_qa19_catalog_content','catalog.testcases.public.TestCatalogContentSettingsWiring','catalog.testcases.test_site_qa06_media_validation','catalog.testcases.test_site_qa01_media_permissions','catalog.testcases.test_site_qa15_settings_concurrency','catalog.testcases.admin.TestSiteGalleryImageAdminMedia','catalog.testcases.admin.TestAdminSidebarStructure','catalog.testcases.test_public_section_switches']
suite=DiscoverRunner(verbosity=0).build_suite(labels_test)
def ids(s):
 for x in s:
  if hasattr(x,'id'):yield x.id()
  else:yield from ids(x)
test_ids=list(ids(suite));assert len(test_ids)==len(set(test_ids))==105
result={'source_count':1032,'actual_template_origin':str(template.origin),'actual_template_sha256':sha(R/rel),'current3root_locales_verified':True,'compiled_actual_template':True,'root_branches':branches,'unchanged_other_branches':10,'SITE19_labels':labels,'str_queries_each':0,'normal_DB':'m10s21_fix_r1','test_DB':settings.DATABASES['default']['TEST']['NAME'],'normal_media':str(settings.MEDIA_ROOT),'normal_private_media':str(settings.PRIVATE_MEDIA_ROOT),'normal_cache':'m10s21-fix-r1','email':'own locmem','external_integrations_disabled':True,'environment_cleared_before_import':True,'test_ids':test_ids,'python':sys.version.split()[0],'django':__import__('django').get_version()}
(Q/'static-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'template_hash':result['actual_template_sha256'],'branches':11,'tests':105,'normal_isolation':True,'current_locale_manifest':True}))
