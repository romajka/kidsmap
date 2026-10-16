"""Disposable loopback-only source/fictional-login endpoints, never deployed."""
import hashlib,json,os
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse
from django.urls import path
from django.template.loader import get_template
from config.urls import urlpatterns as application
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PATHS=['static/css/site.css', 'static/css/motion.css', 'static/js/motion.js', 'src/catalog/templates/base.html', 'src/catalog/templates/pages/owner_team.html', 'src/catalog/templates/pages/owner_reviews.html', 'src/catalog/views.py', 'src/catalog/forms.py', 'src/catalog/controllers/owner_team_controller.py', 'src/catalog/services/business_team.py', 'src/catalog/repositories/django_repositories.py', 'src/catalog/controllers/workflow_notifications.py', 'src/catalog/urls.py', 'src/config/settings.py']
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in PATHS}
START=hashes();assert START==json.loads((HERE/'runtime-source-baseline.json').read_text());TEMPLATE=get_template('pages/owner_team.html')
def allowed(request):return settings.TESTING and request.META.get('REMOTE_ADDR')=='127.0.0.1'
def source(request):
 if not allowed(request):return JsonResponse({},status=403)
 import catalog.controllers.owner_team_controller as controller
 import catalog.services.business_team as service
 from django.db import connection,transaction
 with transaction.atomic():
  with connection.cursor()as cursor:
   cursor.execute('SET TRANSACTION READ ONLY');cursor.execute("SET LOCAL statement_timeout='10s'");cursor.execute('SHOW server_version');pg=cursor.fetchone()[0]
 return JsonResponse({'pid':os.getpid(),'root':str(ROOT),'testing':settings.TESTING,'startup_matches_disk':START==hashes(),'source':START,'loaded_module_paths':{'controller':controller.__file__,'service':service.__file__},'template_origin':str(TEMPLATE.origin),'loaded_template_sha256':hashlib.sha256(TEMPLATE.template.source.encode()).hexdigest(),'sole_locale_paths':[str(p)for p in settings.LOCALE_PATHS],'cache':settings.CACHES['default']['BACKEND'],'email_backend':settings.EMAIL_BACKEND,'postgres':pg,'env_loaded':False,'egress':'only own PostgreSQL'})
def fixtures(request):
 if not allowed(request):return JsonResponse({},status=403)
 data=json.loads((settings.QA_ROOT/'fixtures.json').read_text());data['password']=json.loads((settings.QA_ROOT/'credentials.json').read_text())['login_password'];return JsonResponse(data)
from django.db import connection,transaction
from django.views.decorators.http import require_GET,require_POST
@require_GET
def state(request):
 if not allowed(request):return JsonResponse({},status=403)
 from catalog.models import OwnerTeamInvitation,OwnerTeamMembership,WorkflowNotification,EmailOutbox
 with transaction.atomic():
  with connection.cursor()as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
  d={'invitations':[{'id':r.pk,'status':r.status,'email':r.email,'role':r.role,'place_id':r.place_id,'responded':r.responded_at is not None}for r in OwnerTeamInvitation.objects.order_by('pk')],'memberships':[{'id':r.pk,'member_id':r.member_id,'place_id':r.place_id,'role':r.role,'version':r.version,'active':r.is_active}for r in OwnerTeamMembership.objects.order_by('pk')],'notifications':WorkflowNotification.objects.count(),'outbox':EmailOutbox.objects.count(),'read_only':True}
 return JsonResponse(d)
@require_POST
def tick(request):
 if not allowed(request):return JsonResponse({},status=403)
 from catalog.services.workflow_notifications import deliver_batch
 return JsonResponse({'delivery':deliver_batch(limit=100),'scheduler':'SIMULATED manual tick, actual own filebased email'})
@require_POST
def evidence(request,batch):
 if not allowed(request):return JsonResponse({},status=403)
 data=json.loads(request.body);assert isinstance(data,dict) and isinstance(data.get('rows'),list)
 directory=settings.QA_ROOT/'progress';directory.mkdir(exist_ok=True);target=directory/(batch+'.json');temp=directory/(batch+'.writing');temp.write_text(json.dumps(data,ensure_ascii=False));temp.replace(target)
 return JsonResponse({'saved':True})
urlpatterns=[path('qa/evidence/<slug:batch>/',evidence),path('qa/source/',source),path('qa/fixtures/',fixtures),path('qa/state/',state),path('qa/mail-tick/',tick)]+application
