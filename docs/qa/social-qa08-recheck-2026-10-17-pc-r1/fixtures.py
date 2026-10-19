import json
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from catalog.models import Organization
from catalog.testcases.utils import create_ready_place
@transaction.atomic
def seed():
 U=get_user_model();assert not U.objects.exists();cases=[]
 for kind in ['place','organization']:
  for lang in ['ru','az','en']:
   for width in [360,390,768,1024,1280,1440]:
    key=f'{kind}-{lang}-{width}';owner=U.objects.create_user('s08-owner-'+key,email='owner-'+key+'@example.invalid');recipient=U.objects.create_user('s08-recipient-'+key,email='recipient-'+key+'@example.invalid')
    target=create_ready_place(owner=owner,created_by=owner,name='Fictional '+key) if kind=='place' else Organization.objects.create(owner=owner,created_by=owner,name_az='Fictional '+key)
    cases.append(dict(key=key,kind=kind,lang=lang,width=width,owner=owner.username,recipient=recipient.username,email=recipient.email,target_id=target.pk))
 (settings.QA_ROOT/'cases.json').write_text(json.dumps(cases,indent=2))
 print('36independent fictional owner/recipient/target cases; no invitations until native owner UI')
