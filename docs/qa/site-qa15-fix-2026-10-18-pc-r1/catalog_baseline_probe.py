import ast,hashlib,json,sys
from pathlib import Path
O=Path(__file__).resolve().parent
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site15-pc-fix-r1');sys.argv=['runtime.py','catalog-baseline'];from runtime import *
from catalog.models import CatalogContentSettings
from django.contrib import admin
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from catalog.domain_admin.site import CatalogContentSettingsAdmin
from django.db import transaction,connection
entry=json.loads((O/'source-entry.json').read_text());rel='src/catalog/models/site.py';assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==entry['sources'][rel]
def section(s):
 t=ast.parse(s);return ast.dump(next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='CatalogContentSettingsAdmin'))
assert section((O/'entry-source/src/catalog/domain_admin/site.py').read_text())==section((ROOT/'src/catalog/domain_admin/site.py').read_text())
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'")
 obj=CatalogContentSettings.objects.get(pk=1);request=RequestFactory().get('/admin/catalog/catalogcontentsettings/1/change/');request.user=get_user_model().objects.get(username='site15_super')
 failures={}
 for name,fn in [('model_str',lambda:str(obj)),('current_admin',lambda:admin.site._registry[CatalogContentSettings].changeform_view(request,'1'))]:
  try:fn()
  except TypeError as e:failures[name]=str(e)
assert set(failures)=={'model_str','current_admin'} and all('__str__ returned non-string' in x for x in failures.values()),failures
result={'preexisting_source_model_sha256':entry['sources'][rel],'model_source_unchanged':True,'CatalogContentSettingsAdmin_AST_unchanged':True,'errors':failures,'render_stage':'ModelAdmin str(obj) before render_change_form/template','classification':'Existing baseline direct UI500; out of SITE15 scope. Current Gallery consumer tested natively; Catalog UI beyond failure NOT RUN. No model/assertion fix to obtain green.'}
(QA/'catalog-baseline.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
