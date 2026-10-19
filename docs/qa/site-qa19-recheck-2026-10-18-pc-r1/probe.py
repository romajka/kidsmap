import json,sys,traceback
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/site19-pc-plan-r1';O=Path(__file__).resolve().parent
sys.path.insert(0,str(Q));sys.argv=['runtime.py','probe'];from runtime import *
from catalog.models import CatalogContentSettings
from django.contrib import admin
from django.db import transaction,connection
from django.test import Client
from django.contrib.auth import get_user_model
from django.utils.translation import gettext,override
from django.conf import settings
from django.apps import apps
rows=[]
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
 obj=CatalogContentSettings.objects.get(pk=1)
 for lang in ['az','ru','en']:
  with override(lang):
   row={'lang':lang,'current_gettext':gettext('Контент каталога'),'raw_dunder_return_type':type(obj.__str__()).__name__}
   try:str(obj)
   except TypeError as exc:row['str_error']=str(exc)
   rows.append(row)
import logging
logging.disable(logging.CRITICAL)
client=Client();client.force_login(get_user_model().objects.get(username='site19_super'));client.cookies['django_language']='en'
try:client.get('/admin/catalog/catalogcontentsettings/1/change/')
except TypeError as exc:
 frames=[{'file':Path(x.filename).as_posix().replace(str(R)+'/', ''),'function':x.name,'line':x.lineno} for x in traceback.extract_tb(exc.__traceback__)]
 failure={'exception':type(exc).__name__,'message':str(exc),'frames':frames}
else:raise AssertionError('Expected pre-render str error')
result={'model':rows,'admin':failure,'registered_base_model':CatalogContentSettings in admin.site._registry,'catalog_content_proxy_app_installed':apps.is_installed('catalog.proxy_apps.catalog_content'),'environment':{'testing':settings.TESTING,'normal_database':'m10s19_plan_r1','cache':'locmem','email':'locmem','external_integrations':'disabled','locales':list(map(str,settings.LOCALE_PATHS)),'media':str(settings.MEDIA_ROOT)}}
(Q/'root-cause.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'rows':rows,'error':failure['message'],'last_frame':frames[-1],'registered_base':result['registered_base_model'],'proxy_installed':result['catalog_content_proxy_app_installed']},ensure_ascii=False))
