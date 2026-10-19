import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site08-pc-plan-r1'
code='''import sys,json,re
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/site08-pc-plan-r1');sys.path.insert(0,str(Q));sys.argv=['runtime.py','probe'];from runtime import *
from django.template import engines
from django.contrib import admin
O=Path('/mnt/c/kidsmap/docs/qa/site-qa08-recheck-2026-10-18-pc-r1')
source=(O/'candidate/src/catalog/templates/admin/catalog/shared_settings_change_form.html').read_text();compiled=engines['django'].from_string(source)
t=engines['django'].from_string(re.search(r'<div id="content-main" class="[^"]+">',source).group(0));rows=[]
for model,a in admin.site._registry.items():
 if getattr(a,'change_form_template',None)!='admin/catalog/shared_settings_change_form.html':continue
 for permission in [False,True]:
  html=t.render({'opts':model._meta,'has_change_permission':permission,'adminform':[],'inline_admin_formsets':[],'has_delete_permission':False})
  root=re.search(r'<div id="content-main" class="([^"]+)"',html).group(1).split()
  assert all(c in root for c in ['km-place-form-page','km-settings-form-page','col-12']) and ('km-settings-form-page--editable' in root)==permission
  rows.append({'model':model._meta.model_name,'has_change_permission':permission,'root':root,'CSS_link':"admin/css/pages/kidsmap_settings_forms.css" in source})
assert len(rows)==18 and all(r['CSS_link'] for r in rows)
print(json.dumps({'candidate_compile':True,'branches':rows,'application_sources_unchanged':len(entry['sources']),'candidate_not_applied':True,'actual_source_GREEN':'NOT RUN'}))
'''
(Q/'candidate_probe_own.py').write_text(code);cmd=['docker','exec','m10s08-plan-r1-app','python',str(Q/'candidate_probe_own.py')];r=subprocess.run(cmd,capture_output=True,text=True);(Q/'candidate-probe.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr[-700:];data=json.loads(r.stdout);(O/'evidence/candidate-static.json').write_text(json.dumps(data,indent=2));print(json.dumps({'candidate_compile':True,'branches':len(data['branches']),'candidate_not_applied':True}))
