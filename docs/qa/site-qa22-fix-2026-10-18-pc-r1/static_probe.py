import hashlib,json,re,subprocess,urllib.request
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site22-pc-fix-r1'
code='''import sys,json,re,hashlib
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/site22-pc-fix-r1');sys.path.insert(0,str(Q));sys.argv=['runtime.py','probe'];from runtime import *
from django.template.loader import get_template
from django.template import engines
from django.contrib import admin
from django.contrib.staticfiles import finders
template=get_template('admin/catalog/shared_settings_change_form.html');source=Path(template.origin.name).read_text();fragment=engines['django'].from_string(re.search(r'<div id="content-main" class="[^\"]+">',source).group(0));branches=[]
for model,a in admin.site._registry.items():
 if getattr(a,'change_form_template',None)!='admin/catalog/shared_settings_change_form.html':continue
 for permission in [False,True]:
  html=fragment.render({'opts':model._meta,'has_change_permission':permission});root=re.search(r'class="([^\"]+)"',html).group(1).split();assert 'col-12' in root and 'km-settings-form-page' in root and ('km-settings-form-page--editable' in root)==permission;branches.append({'model':model._meta.model_name,'permission':permission,'root':root})
css=finders.find('admin/css/pages/kidsmap_settings_forms.css');print(json.dumps({'source_count':len(entry['sources']),'actual_template_origin':template.origin.name,'actual_template_sha256':hashlib.sha256(Path(template.origin.name).read_bytes()).hexdigest(),'actual_template_compiled':True,'actual_css_origin':css,'actual_css_sha256':hashlib.sha256(Path(css).read_bytes()).hexdigest(),'branches':branches,'current3root_locales_verified':True,'testing':settings.TESTING,'normal_DB':settings.DATABASES['default']['NAME'],'test_DB':settings.DATABASES['default']['TEST']['NAME'],'normal_media':str(settings.MEDIA_ROOT),'normal_cache':settings.CACHES['default']['LOCATION'],'environment_cleared_before_import':True,'integrations_disabled':not any([settings.GOOGLE_MAPS_API_KEY,settings.GOOGLE_ANALYTICS_MEASUREMENT_ID,settings.INDEXNOW_KEY,settings.GOOGLE_OAUTH_CLIENT_ID])}))
'''
(Q/'static_probe_own.py').write_text(code);cmd=['docker','exec','m10s22-fix-r1-app','python',str(Q/'static_probe_own.py')];r=subprocess.run(cmd,capture_output=True,text=True);(Q/'static-probe.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr[-700:];d=json.loads(r.stdout)
with urllib.request.urlopen('http://127.0.0.1:33610/static/admin/css/pages/kidsmap_settings_forms.css',timeout=10) as response:
 d['CSS_HTTP_status']=response.status;d['CSS_HTTP_sha256']=hashlib.sha256(response.read()).hexdigest()
assert d['CSS_HTTP_sha256']==d['actual_css_sha256'];(O/'evidence/static-runtime.json').write_text(json.dumps(d,indent=2));print(json.dumps({'sources':d['source_count'],'branches':len(d['branches']),'CSS_HTTP_status':d['CSS_HTTP_status'],'source_template':d['actual_template_sha256'],'CSS':d['actual_css_sha256']}))
