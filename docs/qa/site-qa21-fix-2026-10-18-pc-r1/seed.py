import sys,json
from pathlib import Path
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q));sys.argv=['runtime.py','seed-own'];from runtime import *
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from catalog.models import CatalogContentSettings,SiteSettings
assert get_user_model().objects.count()==0
sys.path.insert(0,str(ROOT/'docs/qa/site-qa21-fix-2026-10-18-pc-r1'))
from test_site19_candidate import INITIAL
obj=CatalogContentSettings.get_solo()
for k,v in INITIAL.items():setattr(obj,k,v)
obj.save();assert obj.pk==1
SiteSettings.get_solo()
for role in ['super','editor','viewer','denied']:
 user=get_user_model().objects.create_user('site21_'+role,'site21_'+role+'@example.invalid','fictional',is_staff=True,is_superuser=role=='super')
 if role in ['editor','viewer']:
  codes=['view_catalogcontentsettings']+(['change_catalogcontentsettings'] if role=='editor' else [])
  perms=Permission.objects.filter(content_type__app_label='catalog',codename__in=codes);assert perms.count()==len(codes);user.user_permissions.add(*perms)
print(json.dumps({'synthetic_users':4,'content_pk':obj.pk,'model_source_guard':True,'production_data':False}))
