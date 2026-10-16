"""Testing-only loopback evidence. Never mount in application routes."""
from pathlib import Path
import json
from django.http import JsonResponse,Http404
from django.conf import settings
from django.db import transaction,connection
def mail(request):
 if not settings.TESTING or request.META.get('REMOTE_ADDR') not in ['127.0.0.1','::1']:raise Http404
 p=Path(settings.QA_ROOT)/'mail.json';data=json.loads(p.read_text(encoding='utf-8')) if p.exists() else []
 # Codes and reset links travel in memory only; driver never records this payload.
 return JsonResponse({'messages':data})
def state(request):
 if not settings.TESTING or request.META.get('REMOTE_ADDR') not in ['127.0.0.1','::1']:raise Http404
 from django.contrib.auth import get_user_model
 from catalog.models import OwnerTeamMembership,OwnerTeamInvitation,OrganizationGrant,OrganizationTeamInvitation,Place,SpecialistDocument,UserEmailVerification,AccountDeletionRequest
 with transaction.atomic():
  with connection.cursor() as cur:cur.execute('SET TRANSACTION READ ONLY');cur.execute("SET LOCAL statement_timeout='10s'");cur.execute("SET LOCAL lock_timeout='2s'")
  d={'users':list(get_user_model().objects.values('id','username','is_active','first_name','last_name')),'verified':list(UserEmailVerification.objects.values('user_id','email','is_verified','attempts_left')),'members':list(OwnerTeamMembership.objects.values('id','place_id','member_id','role','is_active','version')),'invitations':list(OwnerTeamInvitation.objects.values('id','place_id','email','status')),'org_grants':list(OrganizationGrant.objects.values('id','organization_id','member_id','role','is_active','version','scope')),'org_invitations':list(OrganizationTeamInvitation.objects.values('id','organization_id','email','status')),'places':list(Place.objects.values('id','owner_id','created_by_id','ownership_version','content_version','status')),'documents':list(SpecialistDocument.objects.values('id','status','is_published','opted_in_by_id')),'deletions':list(AccountDeletionRequest.objects.values('id','user_id','subject_reference','status','scheduled_for'))}
 return JsonResponse(d)
