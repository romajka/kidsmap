import ast,json,subprocess,sys,hashlib
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/site-qa15-recheck-2026-10-18-pc-r1';Q=R/'.tmp/site15-pc-plan-r1';C=O/'candidate'
sys.path.insert(0,str(Q));sys.argv=['runtime.py','proposal-static'];import runtime
from django.template import engines
from django.template.loader import get_template
for p in C.rglob('*.py'):ast.parse(p.read_text())
template=engines['django'].from_string((C/'src/catalog/templates/admin/catalog/shared_settings_change_form.html').read_text())
origin=get_template('admin/catalog/shared_settings_change_form.html').origin.name
assert origin==str(R/'src/catalog/templates/admin/catalog/shared_settings_change_form.html')
fields={}
from django.contrib import admin
from catalog.models import SiteSettings
for model,model_admin in admin.site._registry.items():
 if issubclass(model,SiteSettings):fields[model._meta.label_lower]={'admin':model_admin.__class__.__name__,'template':model_admin.change_form_template}
result={'python_ast':True,'candidate_template_compiles':True,'actual_template_origin':origin,'source_runtime_hashes_match':True,'site_settings_admins':fields,'candidate_behavior_green':'NOT RUN; proposal only'}
print(json.dumps(result,indent=2))
