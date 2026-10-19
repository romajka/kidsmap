import json
from pathlib import Path
Q=Path(__file__).resolve().parent
(Q/'fixtures.py').write_text('''import json
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
''')
(Q/'qa_urls.py').write_text('''import hashlib,json,platform
from django.conf import settings
from django.contrib.auth import get_user_model,login
from django.db import transaction,connection
from django.http import JsonResponse
from django.shortcuts import redirect
from django.template.loader import get_template
from django.urls import path
from catalog.models import WorkflowNotification,OwnerTeamInvitation,OrganizationTeamInvitation,OwnerTeamMembership,OrganizationGrant,EmailOutbox

def case(key):return next(c for c in json.loads((settings.QA_ROOT/'cases.json').read_text()) if c['key']==key)
def fixture_login(request,key,role):
 assert role in ('owner','recipient')
 login(request,get_user_model().objects.get(username=case(key)[role]),backend='django.contrib.auth.backends.ModelBackend')
 return redirect('account_notifications')
def info(request):
 import django
 with connection.cursor() as c:c.execute('SHOW server_version');pg=c.fetchone()[0]
 paths=['src/catalog/controllers/workflow_notifications.py','src/catalog/templates/pages/account_notifications.html','src/catalog/services/business_team.py']
 return JsonResponse(dict(testing=settings.TESTING,python=platform.python_version(),django=django.get_version(),postgresql=pg,source_files=1022,template=get_template('pages/account_notifications.html').origin.name,hashes={p:hashlib.sha256((settings.BASE_DIR/p).read_bytes()).hexdigest() for p in paths},sole_locales=list(map(str,settings.LOCALE_PATHS))))
def state(request,key):
 row=case(key);u=get_user_model().objects.get(username=row['recipient']);model=OwnerTeamInvitation if row['kind']=='place' else OrganizationTeamInvitation
 with transaction.atomic():
  with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
  inv=model.objects.filter(email=u.email).first();notices=WorkflowNotification.objects.filter(recipient_user=u,event_kind='team_invitation')
  return JsonResponse(dict(invitation_id=inv.pk if inv else None,notice_id=notices.first().pk if notices.exists() else None,status=inv.status if inv else None,notification_count=notices.count(),read_count=notices.filter(read_at__isnull=False).count(),memberships=OwnerTeamMembership.objects.filter(member=u,is_active=True).count(),grants=OrganizationGrant.objects.filter(member=u,is_active=True).count(),outbox=EmailOutbox.objects.count()))
from config.urls import urlpatterns as app_urls
urlpatterns=[path('qa/login/<str:key>/<str:role>/',fixture_login),path('qa/info/',info),path('qa/state/<str:key>/',state)]+app_urls
''')
(Q/'browser-initial.js').write_text('''async (page)=>{await page.context().route('**/*',r=>{const u=new URL(r.request().url());return u.hostname==='127.0.0.1'&&u.port==='33358'?r.continue():r.abort('blockedbyclient');});await page.goto('http://127.0.0.1:33358/qa/info/');return {browser:page.context().browser().version(),info:await page.locator('body').innerText()};}''')
print('New owned fixtures and bounded read-only state routes prepared')
