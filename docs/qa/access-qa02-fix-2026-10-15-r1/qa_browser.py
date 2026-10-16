"""Loopback QA fixtures/readback and local scheduler tick; no product routes or production use."""
import json
from pathlib import Path
from django.conf import settings
from django.db import connection,transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET,require_POST
from catalog.models import (OwnerTeamInvitation,OrganizationTeamInvitation,OwnerTeamMembership,
                            OrganizationGrant,WorkflowNotification,EmailOutbox)
from qa_urls import allowed

def fixture(key):
 f=json.loads((settings.QA_ROOT/'fixtures.json').read_text())
 if key not in f['users']:raise ValueError('Not an owned fixture')
 return f,f['users'][key]

@require_GET
def state(request,key):
 if not allowed(request):return JsonResponse({},status=403)
 f,user=fixture(key);rows={}
 with transaction.atomic():
  with connection.cursor()as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
  for kind,model,grants,field in [('place',OwnerTeamInvitation,OwnerTeamMembership,'place'),('organization',OrganizationTeamInvitation,OrganizationGrant,'organization')]:
   row=model.objects.filter(email=user['email']).order_by('-pk').first()
   if row:
    notices=WorkflowNotification.objects.filter(event_kind='team_invitation',entity_type=f'{kind}_team_invitation',entity_id=row.pk,entity_version=1)
    rows[kind]={'invitation_id':row.pk,'target_id':getattr(row,field+'_id'),'notification_id':notices.get().pk,'status':row.status,'responded':row.responded_at is not None,'active_grants':grants.objects.filter(member_id=user['id'],is_active=True).count(),'decision_count':WorkflowNotification.objects.filter(event_kind='team_invitation_decision',entity_type=f'{kind}_team_invitation',entity_id=row.pk).count()}
 return JsonResponse({'key':key,'rows':rows,'read_only':True})

@require_POST
def mail_tick(request):
 if not allowed(request):return JsonResponse({},status=403)
 from catalog.services.workflow_notifications import deliver_batch
 counts=deliver_batch(limit=500)
 return JsonResponse({'delivery':counts,'file_count':len(list(Path(settings.EMAIL_FILE_PATH).glob('*.log'))),'scheduler':'SIMULATED manual tick; real own filebased email'})

@require_POST
def stale_fixture(request):
 if not allowed(request):return JsonResponse({},status=403)
 data=json.loads(request.body);key=data['key'];kind=data['kind'];f,user=fixture(key)
 if key.startswith('email_'):
  from django.contrib.auth import get_user_model
  get_user_model().objects.filter(pk=user['id']).update(email='changed_'+key+'@example.invalid')
 elif key.startswith('expiry_'):
  from datetime import timedelta
  model={'place':OwnerTeamInvitation,'organization':OrganizationTeamInvitation}[kind]
  row=model.objects.filter(email=user['email'],status='PENDING').get()
  model.objects.filter(pk=row.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
 else:return JsonResponse({},status=400)
 return JsonResponse({'fixture_change':'SIMULATED stale email/expiry setup only','kind':kind})

@require_POST
def evidence(request,batch):
 if not allowed(request):return JsonResponse({},status=403)
 data=json.loads(request.body)
 if not isinstance(data,dict)or not isinstance(data.get('rows'),list):return JsonResponse({},status=400)
 directory=settings.QA_ROOT/'progress';directory.mkdir(exist_ok=True)
 path=directory/(batch+'.json');temp=directory/(batch+'.writing')
 temp.write_text(json.dumps(data,ensure_ascii=False));temp.replace(path)
 return JsonResponse({'saved':True,'rows':len(data['rows'])})
