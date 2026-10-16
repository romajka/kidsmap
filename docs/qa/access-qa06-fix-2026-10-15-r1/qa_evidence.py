"""Own TESTING-only loopback endpoints. No code or tokens in returned state."""
import json
from django.http import JsonResponse,Http404
from django.conf import settings
from django.db import transaction,connection
from pathlib import Path
def allowed(request):
 if not settings.TESTING or request.META.get('REMOTE_ADDR')!='127.0.0.1':raise Http404

def mail(request):
 allowed(request);p=settings.QA_ROOT/'mail.json'
 return JsonResponse({'messages':json.loads(p.read_text())if p.exists()else[]})
def state(request):
 allowed(request)
 from django.contrib.auth import get_user_model
 from catalog.models import AccountDeletionRequest
 with transaction.atomic():
  with connection.cursor()as cur:
   cur.execute('SET TRANSACTION READ ONLY');cur.execute("SET LOCAL statement_timeout='5s'");cur.execute("SET LOCAL lock_timeout='2s'")
  users=list(get_user_model().objects.values('id','username','is_active'))
  deletions=[{'id':d.pk,'user_id':d.user_id,'status':d.status,'attempts':d.confirmation_attempts_left,'has_code':bool(d.confirmation_code_hash)}for d in AccountDeletionRequest.objects.all()]
 return JsonResponse({'read_only':True,'synthetic_only':True,'users':users,'deletions':deletions})
