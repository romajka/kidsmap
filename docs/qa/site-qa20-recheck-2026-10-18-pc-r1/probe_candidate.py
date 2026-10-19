import itertools,json,sys
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/site20-pc-plan-r1');sys.path.insert(0,str(Q));sys.argv=['runtime.py','probe-candidate'];from runtime import *
from django.contrib.auth import get_user_model
from django.contrib import admin
from django.template import Context,Engine
from django.test import Client
from django.test.utils import setup_test_environment
from django.urls import reverse
from catalog.models import SiteSettings,CatalogContentSettings,SiteGalleryImage
setup_test_environment()
O=ROOT/'docs/qa/site-qa20-recheck-2026-10-18-pc-r1'
candidate=Engine.get_default().from_string((O/'candidate/src/catalog/templates/admin/catalog/shared_settings_change_form.html').read_text())
models=('sitebrandingsettings','siteaboutsettings','sitecontactssettings','sitefootersettings','siteemptystatesettings','sitevisibilitysettings','siteanalytics','catalogcontentsettings','sitegalleryimage')
rows=[];client=Client()
for role in ('all_viewer','all_editor','gallery_adder','gallery_deleter'):
 client.force_login(get_user_model().objects.get(username='site08_'+role))
 for model in models if role in ('all_viewer','all_editor') else ('sitegalleryimage',):
  add=role=='gallery_adder';url=reverse('admin:catalog_'+model+('_add' if add else '_change'),args=[] if add else [1])
  response=client.get(url);assert response.status_code==200
  ctx={}
  for context in response.context:ctx.update(context.flatten())
  rendered=candidate.render(Context(ctx));save=role in ('all_editor','gallery_adder');delete=role=='gallery_deleter'
  checks={'save':('name="_save"' in rendered)==save,'continue':('name="_continue"' in rendered)==save,'editable':('km-settings-form-page--editable' in rendered)==save,'delete':('deletelink' in rendered)==delete,'card':('km-place-sidebar-card--actions' in rendered)==(save or delete)}
  rows.append({'role':role,'model':model,'checks':checks});assert all(checks.values()),rows[-1]
# Validate Django template boolean precedence independently across every input combination.
truth=[]
for add,change,has_add,has_delete in itertools.product((False,True),repeat=4):
 ctx.update(add=add,has_change_permission=change,has_add_permission=has_add,has_delete_permission=has_delete)
 rendered=candidate.render(Context(ctx));save=change or (add and has_add);delete=has_delete and not add
 checks={'save':('name="_save"' in rendered)==save,'continue':('name="_continue"' in rendered)==save,'editable':('km-settings-form-page--editable' in rendered)==save,'delete':('deletelink' in rendered)==delete,'card':('km-place-sidebar-card--actions' in rendered)==(save or delete)}
 truth.append({'add':add,'change':change,'has_add':has_add,'has_delete':has_delete,'checks':checks});assert all(checks.values()),truth[-1]
runtime_consumers=[]
for model,model_admin in admin.site._registry.items():
 if getattr(model_admin,'change_form_template',None)=='admin/catalog/shared_settings_change_form.html':runtime_consumers.append(model._meta.label_lower)
assert len(runtime_consumers)==9,runtime_consumers
result={'status':'PASS: isolated candidate render only, NOT APPLIED-source GREEN or native candidate evidence','runtime_consumers':sorted(runtime_consumers),'rows':rows,'truth_table':truth,'checks':sum(len(r['checks']) for r in rows+truth),'passed':True,'django_version':django.get_version()}
(Q/'candidate-render.json').write_text(json.dumps(result,indent=2));print(json.dumps({'rows':len(rows),'truth_table':len(truth),'checks':result['checks'],'runtime_consumers':len(runtime_consumers),'status':result['status']}))
