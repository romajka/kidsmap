"""Create an owned source copy and disposable local PostgreSQL audit profile."""
import hashlib,json,os,secrets,shutil,socket,subprocess,time
from pathlib import Path
H=Path(__file__).resolve().parent; R=H.parents[2]; S=R/'.tmp'/H.name
resume=S.exists()
S.mkdir(mode=0o700,exist_ok=True); source=S/'source'; source.mkdir(exist_ok=True)
files={}
for name in ('src','templates','static','locale'):
 if not resume:shutil.copytree(R/name,source/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 for p in (source/name).rglob('*'):
  if p.is_file(): files[str(p.relative_to(source))]=hashlib.sha256(p.read_bytes()).hexdigest()
(H/'source-manifest.json').write_text(json.dumps(files,indent=2))
def port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
cfg=json.loads((S/'config.json').read_text()) if resume else {'pg_port':port(),'http_port':port(),'database':'admin_audit','user':'audit','container':'admin-moderation-fix-20261016-r1-pg'}
secret=json.loads((S/'secrets.json').read_text()) if resume else {'db_password':secrets.token_urlsafe(24),'django_secret':secrets.token_urlsafe(40),'login_password':secrets.token_urlsafe(18)}
(S/'config.json').write_text(json.dumps(cfg));(S/'secrets.json').write_text(json.dumps(secret));os.chmod(S/'secrets.json',0o600)
env=os.environ.copy();env.update(POSTGRES_PASSWORD=secret['db_password'],POSTGRES_USER=cfg['user'],POSTGRES_DB=cfg['database'])
if not resume:subprocess.run(['docker','run','-d','--name',cfg['container'],'--label','kidsmap.qa.run='+H.name,'-e','POSTGRES_PASSWORD','-e','POSTGRES_USER','-e','POSTGRES_DB','-p',f"127.0.0.1:{cfg['pg_port']}:5432",'postgres:17-alpine'],env=env,check=True,capture_output=True)
for _ in range(60):
 if subprocess.run(['docker','exec',cfg['container'],'pg_isready','-U','audit','-d','admin_audit'],capture_output=True).returncode==0:break
 time.sleep(.3)
subprocess.run([str(R/'.venv/bin/python'),str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(source/'locale'),'--output',str(S/'locales'),'--compiler','native','--locales','ru','az','en'],check=True,capture_output=True)
(S/'settings.py').write_text('''from config.settings import *
import json
from pathlib import Path
QA_ROOT=Path(__file__).resolve().parent
cfg=json.loads((QA_ROOT/'config.json').read_text());secret=json.loads((QA_ROOT/'secrets.json').read_text())
SECRET_KEY=secret['django_secret'];DEBUG=True
DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':cfg['database'],'USER':cfg['user'],'PASSWORD':secret['db_password'],'HOST':'127.0.0.1','PORT':cfg['pg_port'],'TEST':{'NAME':'test_admin_audit'}}}
CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'admin-audit'}}
EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
MEDIA_ROOT=QA_ROOT/'media';PRIVATE_MEDIA_ROOT=QA_ROOT/'private-media';STATIC_ROOT=QA_ROOT/'staticfiles'
LOCALE_PATHS=(str(QA_ROOT/'locales/locale'),)
GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_MAP_ID=GOOGLE_ANALYTICS_MEASUREMENT_ID=GOOGLE_ANALYTICS_PROPERTY_ID=GOOGLE_OAUTH_CLIENT_ID=GOOGLE_OAUTH_CLIENT_SECRET=GOOGLE_APPLICATION_CREDENTIALS=INDEXNOW_KEY=''
SOCIALACCOUNT_PROVIDERS={};ADMIN_HOST='';ALLOWED_HOSTS=['127.0.0.1','localhost','testserver','admin.audit.invalid','public.audit.invalid']
PUBLIC_BASE_URL=f"http://localhost:{cfg['http_port']}"
ADMIN_HOST='127.0.0.1'
SESSION_COOKIE_NAME='adminauditsession';CSRF_COOKIE_NAME='csrftoken'
SESSION_COOKIE_SECURE=CSRF_COOKIE_SECURE=SECURE_SSL_REDIRECT=False
ROOT_URLCONF='qa_urls';LOCAL_ANALYTICS_STORAGE_ENABLED=False;OWNER_ANALYTICS_ENABLED=False
STORAGES={'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},'staticfiles':{'BACKEND':'django.contrib.staticfiles.storage.StaticFilesStorage'}}
PLACE_REVIEW_COOLDOWN_SECONDS=0;TASK33_R1_WRITE_MODE='all'
''')
(S/'qa_urls.py').write_text('''from config.urls import urlpatterns as application
from django.urls import path
from django.http import JsonResponse
from django.conf import settings
import json
def fixtures(request):
 assert settings.TESTING and request.META['REMOTE_ADDR']=='127.0.0.1'
 data=json.loads((settings.QA_ROOT/'fixtures.json').read_text());data['password']=json.loads((settings.QA_ROOT/'secrets.json').read_text())['login_password'];return JsonResponse(data)
urlpatterns=[path('admin/qa/fixtures/',fixtures)]+application
''')
(S/'runtime.py').write_text('''import os,sys,socket,json
from pathlib import Path
S=Path(__file__).resolve().parent
for k in list(os.environ):
 if k not in {'PATH','LANG','LC_ALL','TZ'}:os.environ.pop(k)
os.environ.update(DJANGO_TESTING='1',DJANGO_DEBUG='1',DJANGO_SETTINGS_MODULE='settings',PYTHONDONTWRITEBYTECODE='1')
sys.dont_write_bytecode=True;sys.path[:0]=[str(S),str(S/'source/src')]
cfg=json.loads((S/'config.json').read_text());orig=socket.socket.connect
def connect(sock,addr):
 if not isinstance(addr,tuple) or addr[0] not in ('127.0.0.1','localhost') or addr[1]!=cfg['pg_port']:raise RuntimeError('Audit external egress denied')
 return orig(sock,addr)
socket.socket.connect=connect
import django;django.setup()
from django.conf import settings
from django.core.management import call_command
assert settings.TESTING and settings.DATABASES['default']['NAME']=='admin_audit'
for n in ('MEDIA_ROOT','PRIVATE_MEDIA_ROOT','STATIC_ROOT'):Path(getattr(settings,n)).mkdir(exist_ok=True)
if sys.argv[1]=='prepare':
 call_command('migrate',interactive=False,verbosity=0)
 exec(compile((S/'seed.py').read_text(),str(S/'seed.py'),'exec'))
elif sys.argv[1]=='serve':call_command('runserver',f"127.0.0.1:{cfg['http_port']}",use_reloader=False,insecure=True)
elif sys.argv[1]=='test':call_command('test',*sys.argv[2:],interactive=False,verbosity=1)
elif sys.argv[1]=='probe':exec(compile((S/'probe.py').read_text(),str(S/'probe.py'),'exec'))
''')
(S/'seed.py').write_text('''from django.contrib.auth import get_user_model
from catalog.models import UserEmailVerification
from catalog.testcases.utils import create_ready_place
from catalog.services.review_versions import submit_review,moderate_candidate
from django.utils import timezone
from PIL import Image
U=get_user_model();secret=json.loads((S/'secrets.json').read_text());pw=secret['login_password']
staff=U.objects.create_superuser('fictional_reviewer','reviewer@example.invalid',pw)
users=[U.objects.create_user('fictional_author_'+str(i),email=f'author{i}@example.invalid',password=pw,first_name='Fictional') for i in range(4)]
for u in [staff,*users]:UserEmailVerification.objects.update_or_create(user=u,defaults={'email':u.email,'is_verified':True,'verified_at':timezone.now()})
photo=settings.MEDIA_ROOT/'places/audit.png';photo.parent.mkdir(exist_ok=True);Image.new('RGB',(600,600),'#136F38').save(photo)
place=create_ready_place(name='Fictional audit club',name_ru='Вымышленный клуб',name_az='Uydurma dərnək',photo='places/audit.png')
pending=create_ready_place(name='Fictional pending club',name_ru='Вымышленное место на проверке',name_az='Uydurma məkan',status='pending',is_active=False,photo='places/audit.png')
heads=[]
for i,u in enumerate(users):
 h,r=submit_review(target=place,user=u,rating=5,text=f'Fictional original review {i}',author_name='Fictional author',enforce_cooldown=False)
 if i in (1,3):
  moderate_candidate(head=h,revision_id=r.pk,actor=staff,approve=True);h.refresh_from_db()
  h,r=submit_review(target=place,user=u,rating=2,text=f'Fictional EDIT awaiting approval {i}',author_name='Fictional author',expected_revision_id=h.current_revision_id,enforce_cooldown=False)
 heads.append({'head':h.pk,'candidate':r.pk,'scenario':'edit' if i in (1,3) else 'first'})
(S/'fixtures.json').write_text(json.dumps({'username':staff.username,'place':place.pk,'pending_place':pending.pk,'reviews':heads,'synthetic_only':True}))
print('Synthetic fixtures created: 5 users, 2 places, 4 pending candidates')
''')
subprocess.run([str(R/'.venv/bin/python'),str(S/'runtime.py'),'prepare'],check=True,stdout=(S/'prepare.log').open('w'),stderr=subprocess.STDOUT)
with (S/'server.log').open('w') as log:p=subprocess.Popen([str(R/'.venv/bin/python'),str(S/'runtime.py'),'serve'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(H/'environment.json').write_text(json.dumps({'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'source_copy':str(source),'source_files':len(files),'profile':str(S),'http_port':cfg['http_port'],'pg_port':cfg['pg_port'],'container':cfg['container'],'pid':p.pid,'testing':True,'egress':'only own PostgreSQL','credentials_in_artifacts':False},indent=2))
print(json.dumps({'http_port':cfg['http_port'],'pid':p.pid,'source_files':len(files)}))
