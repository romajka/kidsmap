import hashlib,json,platform
from django.conf import settings
from django.contrib.auth import get_user_model,login,logout
from django.db import transaction,connection
from django.http import JsonResponse
from django.shortcuts import redirect
from django.template.loader import get_template
from django.urls import path
from catalog.models import WorkflowNotification,OwnerTeamInvitation,OrganizationTeamInvitation,OwnerTeamMembership,OrganizationGrant,EmailOutbox

def case(key):return next(c for c in json.loads((settings.QA_ROOT/'cases.json').read_text()) if c['key']==key)
def fixture_login(request,key,role):
 assert role in ('owner','recipient','outsider','guest')
 if role=='guest':logout(request)
 else:login(request,get_user_model().objects.get(username='s08-fix-outsider' if role=='outsider' else case(key)[role]),backend='django.contrib.auth.backends.ModelBackend')
 return redirect('account_notifications')
def info(request):
 import django
 with connection.cursor() as c:c.execute('SHOW server_version');pg=c.fetchone()[0]
 paths=['src/catalog/controllers/workflow_notifications.py','src/catalog/templates/pages/account_notifications.html','src/catalog/services/business_team.py']
 return JsonResponse(dict(testing=settings.TESTING,python=platform.python_version(),django=django.get_version(),postgresql=pg,source_files=1023,template=get_template('pages/account_notifications.html').origin.name,hashes={p:hashlib.sha256((settings.BASE_DIR/p).read_bytes()).hexdigest() for p in paths},sole_locales=list(map(str,settings.LOCALE_PATHS))))
def state(request,key):
 row=case(key);u=get_user_model().objects.get(username=row['recipient']);model=OwnerTeamInvitation if row['kind']=='place' else OrganizationTeamInvitation
 with transaction.atomic():
  with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
  inv=model.objects.filter(email=u.email).order_by('-pk').first();notices=WorkflowNotification.objects.filter(recipient_user=u,event_kind='team_invitation').order_by('-pk')
  return JsonResponse(dict(invitation_id=inv.pk if inv else None,notice_id=notices.first().pk if notices.exists() else None,status=inv.status if inv else None,notification_count=notices.count(),read_count=notices.filter(read_at__isnull=False).count(),memberships=OwnerTeamMembership.objects.filter(member=u,is_active=True).count(),grants=OrganizationGrant.objects.filter(member=u,is_active=True).count(),outbox=EmailOutbox.objects.count()))
from config.urls import urlpatterns as app_urls
urlpatterns=[path('qa/login/<str:key>/<str:role>/',fixture_login),path('qa/info/',info),path('qa/state/<str:key>/',state)]+app_urls

