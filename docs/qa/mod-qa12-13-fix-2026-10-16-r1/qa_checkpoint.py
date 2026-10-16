"""Owned testing-only evidence checkpoint. Not an application endpoint."""
import json
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse,Http404
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def checkpoint(request,lang):
 if not settings.TESTING or request.META.get('REMOTE_ADDR')!='127.0.0.1' or lang not in ('ru','az','en')or request.method!='POST' or len(request.body)>5000000:raise Http404
 data=json.loads(request.body)
 if set(data)-{'rows','diagnostics','boundary','source','mode','before','after','complete'}:raise Http404
 (Path(__file__).resolve().parent/('checkpoint-'+lang+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2))
 return JsonResponse({'saved':True,'rows':len(data.get('rows',[]))})
