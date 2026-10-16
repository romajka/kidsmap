import hashlib,json,os
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse
from django.urls import path
from config.urls import urlpatterns as application
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def source():
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for p in (ROOT/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
START=source()
def version(request):
 if request.META.get('REMOTE_ADDR')!='127.0.0.1' or not settings.TESTING: return JsonResponse({},status=403)
 current=source();entry=json.loads((HERE/'entry-final.json').read_text())['source_files']
 from django.db import connection,transaction
 with transaction.atomic():
  with connection.cursor() as c:
   c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'");c.execute('SHOW server_version');pg=c.fetchone()[0]
 from catalog.photo_views import save_owner_photos
 import inspect
 typed='candidate_version_conflict' in inspect.unwrap(save_owner_photos).__code__.co_consts
 from catalog.domain_admin.place import PlaceAdmin
 from catalog.services.permanent_place_wizard import ui_copy
 from django.utils.translation import override
 admin_retention='_km_candidate_conflict' in PlaceAdmin.changeform_view.__code__.co_names
 with override('en'): english_copy=ui_copy()['unsaved_title']=='You have unsaved changes'
 return JsonResponse({'admin_retention_loaded':admin_retention,'new_english_copy_loaded':english_copy,'typed_candidate_conflict_loaded':typed,'testing':settings.TESTING,'pid':os.getpid(),'entry_matches_startup':entry==START,'startup_matches_disk':START==current,'source_files':len(START),'source_digest':hashlib.sha256(json.dumps(START,sort_keys=True).encode()).hexdigest(),'postgres':pg,'database_host':settings.DATABASES['default']['HOST'],'database_port':settings.DATABASES['default']['PORT'],'sole_locale_root':str(settings.LOCALE_PATHS[0]),'cache':settings.CACHES['default']['BACKEND'],'email':settings.EMAIL_BACKEND,'external_egress':'only owned PostgreSQL connect/connect_ex allowed','env_file_loaded':False})
def org_proof(request, organization_id):
 if request.META.get('REMOTE_ADDR')!='127.0.0.1' or not settings.TESTING: return JsonResponse({},status=403)
 from django.db import connection,transaction
 from catalog.models import Organization,ServerDraft
 import catalog.controllers.organization_workspace as controller
 with transaction.atomic():
  with connection.cursor() as c:
   c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
  org=Organization.objects.get(pk=organization_id)
  if org.owner_id!=2 or not org.name_az.startswith('ORGQA01 fictional '):return JsonResponse({},status=403)
  revision=getattr(org,'content_revision',None)
  data={'organization_id':org.pk,'public_id':str(org.public_id),'status':org.status,'content_version':org.content_version,'live_name_en':org.name_en,'revision_id':revision.pk if revision else None,'revision_status':revision.status if revision else None,'revision_version':revision.version if revision else None,'revision_name_en':revision.payload.get('name_en') if revision else None,'drafts':list(ServerDraft.objects.filter(actor_id=2,target_type='organization',target_id=org.pk).values('id','source_version','schema_version','version','fields')),'read_only':True,'controller_source':controller.__file__,'controller_hash':hashlib.sha256(Path(controller.__file__).read_bytes()).hexdigest()}
 return JsonResponse(data)
urlpatterns=[path('qa/start-version/',version),path('qa/org-proof/<int:organization_id>/',org_proof)]+application
