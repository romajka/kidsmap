"""Owned ACCEPT07 AUDIT ONLY runtime; never imports manage.py or checkout .env."""
import hashlib,importlib.util,json,os,socket,sys
sys.dont_write_bytecode=True
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SCRATCH=ROOT/'.tmp'/HERE.name
for key in list(os.environ):
 if key not in {'PATH','LANG','LC_ALL','TZ'}:os.environ.pop(key)
os.environ.update(DJANGO_TESTING='1',DJANGO_DEBUG='1',DJANGO_SETTINGS_MODULE='settings',PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1')
sys.path[:0]=[str(HERE),str(ROOT/'src')]
sys.path.insert(1,str(SCRATCH/'python-deps'))
cfg=json.loads((SCRATCH/'config.json').read_text());connect_original=socket.socket.connect;connect_ex_original=socket.socket.connect_ex
def allowed(addr):return isinstance(addr,tuple)and len(addr)>=2 and addr[0]in('127.0.0.1','localhost')and addr[1]==cfg['pg_port']
def connect(sock,addr):
 if not allowed(addr):raise RuntimeError('QA egress denied')
 return connect_original(sock,addr)
def connect_ex(sock,addr):
 if not allowed(addr):raise RuntimeError('QA egress denied')
 return connect_ex_original(sock,addr)
socket.socket.connect=connect;socket.socket.connect_ex=connect_ex
spec=importlib.util.spec_from_file_location('isolated_locales',ROOT/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
manifest=builder.verify(SCRATCH/'locales/manifest.json',ROOT/'locale');assert manifest['locales']==['ru','az','en']
import gettext
MO_OPENED=[]
_gnu_init=gettext.GNUTranslations.__init__
def tracked_gnu_init(self,fp=None):
 if fp is not None and hasattr(fp,'name'):MO_OPENED.append(str(fp.name))
 return _gnu_init(self,fp)
gettext.GNUTranslations.__init__=tracked_gnu_init
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
assert settings.TESTING and settings.DATABASES['default']['NAME']==cfg['database']and tuple(settings.LOCALE_PATHS)==(manifest['locale_root'],)
for key in ('MEDIA_ROOT','PRIVATE_MEDIA_ROOT','EMAIL_FILE_PATH','STATIC_ROOT'):Path(getattr(settings,key)).mkdir(exist_ok=True)
mode=sys.argv[1]
if mode=='prepare':
 call_command('migrate',interactive=False,verbosity=1)
 STATE=SCRATCH
 exec(compile((HERE/'seed.py').read_text(),str(HERE/'seed.py'),'exec'),globals())
elif mode=='serve':call_command('runserver',f"127.0.0.1:{cfg['http_port']}",use_reloader=False,use_threading=True,insecure=True,verbosity=1)
elif mode=='test':
 settings.EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
 settings.CSRF_COOKIE_NAME='csrftoken'
 settings.MEDIA_ROOT=SCRATCH/'unit-media';settings.PRIVATE_MEDIA_ROOT=SCRATCH/'unit-private-media'
 call_command('test',*sys.argv[2:],interactive=False,verbosity=1)
elif mode=='finalize-owned':
 from datetime import timedelta
 from catalog.models import AccountDeletionRequest,SpecialistDocument,Specialist,Place
 from catalog.services.account_deletion import finalize_account_deletion
 from django.db import transaction,connection
 outcomes=[]
 pending=list(AccountDeletionRequest.objects.filter(status='SCHEDULED').select_related('user').order_by('pk'))
 for d in pending:
  username=d.user.username
  early=finalize_account_deletion(d.pk)
  result=finalize_account_deletion(d.pk,now=d.scheduled_for+timedelta(seconds=1))
  outcomes.append({'user':username,'before_deadline_outcome':early.outcome,'simulated_future_outcome':result.outcome,'counters':result.counters})
 with transaction.atomic():
  with connection.cursor()as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'")
  summary={'deletions_by_status':{},'specialists':list(Specialist.objects.values('pk','owner_id','verified_person_user_id','status')),'documents_retained':SpecialistDocument.objects.count(),'owned_places':list(Place.objects.values('pk','owner_id','created_by_id','ownership_version'))}
  for d in AccountDeletionRequest.objects.values('status'):
   key=d['status'];summary['deletions_by_status'][key]=summary['deletions_by_status'].get(key,0)+1
 (HERE/'finalization.json').write_text(json.dumps({'mode':'SIMULATED future clock on own UI-confirmed fixtures only; canonical service, no direct ORM state transitions','outcomes':outcomes,'read_only_after':summary},indent=2));print(json.dumps({'own_pending_processed':len(outcomes),'outcomes':[{'before':r['before_deadline_outcome'],'future':r['simulated_future_outcome']}for r in outcomes]}))
elif mode=='whitespace-form-proof':
 from catalog.forms import AccountDeletionConfirmForm
 from catalog.services.account_deletion import typed_confirmation_phrase
 rows=[]
 for lang in ('ru','az','en'):
  exact=typed_confirmation_phrase(lang);raw=' '+exact+' '
  form=AccountDeletionConfirmForm(data={'form_action':'confirm','confirmation_code':'000001','typed_confirmation':raw})
  valid=form.is_valid();rows.append({'lang':lang,'field_strip':form.fields['typed_confirmation'].strip,'form_valid':valid,'raw_equals_exact':raw==exact,'cleaned_equals_exact':valid and form.cleaned_data['typed_confirmation']==exact,'raw_length':len(raw),'shown_length':len(exact)})
 (HERE/(sys.argv[2] if len(sys.argv)>2 else 'whitespace-form-proof.json')).write_text(json.dumps({'source':'current WORKTREE AccountDeletionConfirmForm; service strictness already asserted in existing tests','rows':rows},indent=2));print(json.dumps(rows))
elif mode=='runtime-info':
 import pypdf,PIL
 from config import settings as base_settings
 from django.db import transaction,connection
 from django.db.migrations.recorder import MigrationRecorder
 with transaction.atomic():
  with connection.cursor()as c:
   c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute('SELECT current_database(),current_user,version()');db,user,version=c.fetchone()
  migrations=MigrationRecorder.Migration.objects.count()
 result={'read_only':True,'root':str(ROOT),'python':sys.version.split()[0],'interpreter':sys.executable,'django':django.get_version(),'pypdf':pypdf.__version__,'pypdf_origin':pypdf.__file__,'Pillow':PIL.__version__,'database':db,'database_user':user,'postgres':version,'migrations':migrations,'testing':settings.TESTING,'base_code_default_retention_active':bool(base_settings.ACCOUNT_DELETION_RETENTION_POLICY.get('active',False)),'own_policy_version':settings.ACCOUNT_DELETION_RETENTION_POLICY['version'],'sole_locale_paths':[str(p)for p in settings.LOCALE_PATHS],'cache':settings.CACHES['default'],'media':str(settings.MEDIA_ROOT),'private_media':str(settings.PRIVATE_MEDIA_ROOT),'email_backend':settings.EMAIL_BACKEND,'email_path':str(settings.EMAIL_FILE_PATH)}
 (HERE/'runtime-info.json').write_text(json.dumps(result,indent=2));print(json.dumps({'python':result['python'],'Django':result['django'],'pypdf':result['pypdf'],'db':db,'base_policy_active':result['base_code_default_retention_active'],'own_policy':result['own_policy_version'],'migrations':migrations}))
elif mode=='runner-preflight':
 import queue
 from config.test_runner import KidsMapTestRunner
 assert Path(queue.__file__).resolve().is_relative_to(Path(sys.base_prefix))
 print(json.dumps({'stdlib_queue':queue.__file__,'runner':KidsMapTestRunner.__module__+'.'+KidsMapTestRunner.__name__,'test_database':'test_'+cfg['database'],'testing':settings.TESTING}))
elif mode=='test-full':
 exec(compile((HERE/'full_tests.py').read_text(),str(HERE/'full_tests.py'),'exec'),globals())
else:raise SystemExit('Unknown mode')
