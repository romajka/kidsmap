import json
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client
from catalog.models import Event,Specialist,Place
from django.db import transaction,connection
# New synthetic staff identity only; tested domain records remain read-only.
u=get_user_model().objects.create_user('qa_mod08_spec_reader',is_staff=True)
u.user_permissions.add(Permission.objects.get(content_type__app_label='catalog',codename='view_specialist'))
c=Client();c.force_login(u);rows=[]
for lang in ('ru','az','en'):
 c.cookies['django_language']=lang
 prefix='' if lang=='az'else'/'+lang
 for model,expected in (('specialist',200),('event',403),('place',403)):
  response=c.get(prefix+'/admin/catalog/'+model+'/?q=QA+Filter&status__exact=published&sort=name_asc')
  rows.append({'id':'specialist-only reader direct '+model,'lang':lang,'status':'PASS'if response.status_code==expected else'FAIL','http':response.status_code,'expected':expected})
(HERE/'shared-acl.json').write_text(json.dumps({'rows':rows},indent=2));print(json.dumps({'rows':len(rows),'fail':sum(x['status']=='FAIL'for x in rows)}));assert all(x['status']=='PASS'for x in rows)
