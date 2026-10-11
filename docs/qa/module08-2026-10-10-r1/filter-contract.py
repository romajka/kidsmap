"""Read-only source-backed admin metadata; rendered UI evidence is drawers.result."""
import sys,json
sys.argv=['run.py','qa-read-filter-contract'];from run import *
from django.contrib import admin
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.db import transaction,connection
from catalog.models import Event,Specialist
rows=[]
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 user=get_user_model().objects.get(username='qa08_admin')
 for model in [Event,Specialist]:
  instance=admin.site._registry[model];request=RequestFactory().get('/ru/admin/catalog/'+model._meta.model_name+'/');request.user=user
  cl=instance.get_changelist_instance(request)
  rows.append({'model':model._meta.model_name,'primary_filters':instance.km_primary_filters,'list_filters':[str(x) for x in instance.get_list_filter(request)],'filter_specs':[{'class':type(spec).__name__,'field_path':getattr(spec,'field_path',None),'parameter_name':getattr(spec,'parameter_name',None),'title':str(spec.title)} for spec in cl.filter_specs]})
(HERE/'filter-contract.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8');print(json.dumps(rows,ensure_ascii=True))
