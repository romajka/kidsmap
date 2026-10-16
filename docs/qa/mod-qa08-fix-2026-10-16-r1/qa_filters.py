"""Read-only contract evidence over this run's fictional queues only."""
import json
from pathlib import Path
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import connection,transaction
from django.http import JsonResponse,Http404
from django.test import RequestFactory
from django.utils.translation import override
from catalog.models import Place,Event,Specialist

def contract(request,model):
 if not settings.TESTING or request.META.get('REMOTE_ADDR')!='127.0.0.1' or model not in('place','event','specialist'):raise Http404
 with override(request.headers.get('X-QA-Language','az')),transaction.atomic():
  with connection.cursor()as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
  actor=json.loads((Path(__file__).resolve().parent/'fixtures.json').read_text())['actors']['admin'];req=RequestFactory().get('/admin/catalog/'+model+'/',request.GET);req.user=get_user_model().objects.get(username=actor);cl=admin.site._registry[{'place':Place,'event':Event,'specialist':Specialist}[model]].get_changelist_instance(req)
  specs=[{'field':getattr(s,'field_path',None)or getattr(s,'parameter_name',None),'title':str(s.title),'parameters':list(s.expected_parameters()),'choices':[{'display':str(x.get('display','')),'url':x.get('query_string','?'),'selected':bool(x.get('selected'))}for x in s.choices(cl)]}for s in cl.filter_specs]
  return JsonResponse({'model':model,'effective_query':req.GET.urlencode(),'database':settings.DATABASES['default']['NAME'],'read_only':True,'fields':specs,'primary_config':list(getattr(cl.model_admin,'km_primary_filters',())),'result_count':cl.result_count,'result_ids':list(cl.result_list.values_list('pk',flat=True))})
