import inspect,json,sys
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/site21-pc-plan-r1'
sys.path.insert(0,str(Q));sys.argv=['runtime.py','source-probe'];from runtime import *
from django.template.loader import get_template
from django.conf import settings
from django.template import Engine,Context
from django.utils.translation import override
from django.db import connection,transaction
from catalog.models import CatalogContentSettings
origins={}
for name in ['admin/change_form.html','admin/base.html','admin/catalog/shared_settings_change_form.html']:
 p=Path(get_template(name).origin.name);lines=p.read_text().splitlines();hits=[]
 for i,line in enumerate(lines):
  if ('id="content-main"' in line or 'block content' in line or 'class="row"' in line or ('col-12' in line and name=='admin/change_form.html')):hits.append({'line':i+1,'source':line.strip()})
 origins[name]={'path':p.as_posix(),'relevant_lines':hits[:16]}
assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s21_plan_r1' and settings.CACHES['default']['BACKEND'].endswith('LocMemCache')
assert not settings.INDEXNOW_KEY and not settings.SOCIALACCOUNT_PROVIDERS and not settings.GOOGLE_MAPS_API_KEY
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'")
 obj=CatalogContentSettings.objects.get(pk=1)
 labels={}
 for lang in ['az','ru','en']:
  with override(lang):labels[lang]=str(obj)
candidate=(R/'docs/qa/site-qa21-recheck-2026-10-18-pc-r1/candidate/src/catalog/templates/admin/catalog/shared_settings_change_form.html').read_text()
Engine.get_default().from_string(candidate)
root_line=next(x for x in candidate.splitlines() if '<div id="content-main"' in x)
branches={}
for model in ['catalogcontentsettings','sitebrandingsettings','siteaboutsettings','sitecontactssettings','sitefootersettings','siteemptystatesettings','sitevisibilitysettings','siteanalytics','sitesettings','sitegalleryimage','contentcatalogsettings']:
 html=Engine.get_default().from_string(root_line).render(Context({'opts':{'model_name':model}}));branches[model]=html.strip()
 assert (' col-12' in html)==(model=='catalogcontentsettings')
result={'origins':origins,'source_guard':1032,'current3root_locales_verified':True,'model_SITE19_labels':labels,'candidate_template_compile':True,'root_conditional_branches':branches,'candidate_not_applied':True,'candidate_GET_GREEN':'NOT RUN','environment':'cleared before Django import; isolated normal/test DB, own locmem cache/email/media/private; disabled integrations','production':False}
(Q/'source-probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
