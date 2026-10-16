"""Own read-only status probes for already UI-scheduled synthetic accounts."""
import json
from django.conf import settings
from django.http import JsonResponse,Http404
from django.db import connection,transaction
from django.urls import reverse
from django.utils.translation import override
from catalog.models import AccountDeletionRequest
from catalog.services.account_deletion import make_status_token
from pathlib import Path
def status_urls(request):
 if not settings.TESTING or request.META.get('REMOTE_ADDR')!='127.0.0.1':raise Http404
 cells=json.loads((Path(__file__).parent/'fixtures.json').read_text())['cells'];rows=[]
 with transaction.atomic():
  with connection.cursor()as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'")
  for cell in cells:
   d=AccountDeletionRequest.objects.get(user_id=cell['user_id']);assert d.status=='SCHEDULED'
   with override(cell['lang']):path=reverse('account_deletion_status',args=[d.subject_reference])
   rows.append({**cell,'url':path+'?token='+make_status_token(d.subject_reference)})
 return JsonResponse({'mode':'READ ONLY canonical signed URL probe, not new native redirect evidence','rows':rows})
