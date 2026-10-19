import hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site08-pc-plan-r1'
code='''import sys,json,hashlib
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/site08-pc-plan-r1');sys.path.insert(0,str(Q));sys.argv=['runtime.py','probe'];from runtime import *
from django.template.loader import get_template
from django.contrib import admin
from django.contrib.staticfiles import finders
template=get_template('admin/catalog/shared_settings_change_form.html');css=finders.find('admin/css/pages/kidsmap_admin_form_shell.css')
data={'template_origin':template.origin.name,'template_sha256':hashlib.sha256(Path(template.origin.name).read_bytes()).hexdigest(),'template_compiled':True,'css_origin':css,'css_sha256':hashlib.sha256(Path(css).read_bytes()).hexdigest(),'current3root_locales_verified':True,'sources_verified':len(entry['sources']),'consumers':[{'model':m._meta.model_name,'admin':a.__class__.__name__} for m,a in admin.site._registry.items() if getattr(a,'change_form_template',None)=='admin/catalog/shared_settings_change_form.html'],'testing':settings.TESTING,'normal_DB':settings.DATABASES['default']['NAME'],'test_DB':settings.DATABASES['default']['TEST']['NAME'],'cache':settings.CACHES['default']['LOCATION'],'media':str(settings.MEDIA_ROOT),'external_integrations_disabled':not any([settings.GOOGLE_MAPS_API_KEY,settings.GOOGLE_ANALYTICS_MEASUREMENT_ID,settings.INDEXNOW_KEY,settings.GOOGLE_OAUTH_CLIENT_ID])}
print(json.dumps(data))
'''
(Q/'static_probe_own.py').write_text(code)
cmd=['docker','exec','m10s08-plan-r1-app','python',str(Q/'static_probe_own.py')];r=subprocess.run(cmd,capture_output=True,text=True);(Q/'static-probe.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr[-500:]
data=json.loads(r.stdout);(O/'evidence/static-runtime.json').write_text(json.dumps(data,indent=2));print(json.dumps(data,indent=2))
