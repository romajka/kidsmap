"""New isolated approved04 runtime; never imports manage.py or checkout .env."""
import hashlib,importlib.util,json,os,socket,sys
sys.dont_write_bytecode=True
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SCRATCH=ROOT/'.tmp'/HERE.name
for key in list(os.environ):
 if key not in {'PATH','LANG','LC_ALL','TZ'}:os.environ.pop(key)
os.environ.update(DJANGO_TESTING='1',DJANGO_DEBUG='1',DJANGO_SETTINGS_MODULE='settings',PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1')
sys.path[:0]=[str(HERE),str(ROOT/'src')]
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
 from django.contrib.auth import get_user_model
 from catalog.models import UserEmailVerification
 from django.utils import timezone
 password=json.loads((SCRATCH/'credentials.json').read_text())['login_password'];users={}
 for lang in ('ru','az','en'):
  for width in (360,390,768,1024,1280,1440):
   key=f'{lang}_{width}';u=get_user_model().objects.create_user(username='qa05_'+key,email='qa05_'+key+'@example.invalid',password=password)
   UserEmailVerification.objects.create(user=u,email=u.email,is_verified=True,verified_at=timezone.now())
   users[key]={'username':u.username,'email':u.email,'id':u.pk}
 (SCRATCH/'fixtures.json').write_text(json.dumps({'users':users}));print('Prepared own DB:18 fictional verified users; no seeded deletion requests; SIMULATED TEST_POLICY')
elif mode=='serve':call_command('runserver',f"127.0.0.1:{cfg['http_port']}",use_reloader=False,use_threading=True,insecure=True,verbosity=1)
elif mode=='test':
 settings.EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
 call_command('test',*sys.argv[2:],interactive=False,verbosity=1)
elif mode=='mailproof':
 import email,re
 from django.db import transaction,connection
 from django.contrib.auth.hashers import check_password
 from catalog.models import AccountDeletionRequest
 messages={}
 for file in Path(settings.EMAIL_FILE_PATH).glob('*'):
  for chunk in file.read_text().split('\n'+'-'*79+'\n'):
   msg=email.message_from_string(chunk.lstrip());payload=msg.get_payload(decode=True)
   if payload:
    codes=re.findall(r'(?<!\d)\d{6}(?!\d)',payload.decode(msg.get_content_charset() or 'utf-8'))
    if codes:messages[msg.get('To','').strip()]=codes[-1]
 rows=[]
 with transaction.atomic():
  with connection.cursor()as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'")
  for deletion in AccountDeletionRequest.objects.select_related('user').order_by('user__username'):
   rows.append({'user':deletion.user.username,'local_mail_code_matches_own_request':check_password(messages.get(deletion.user.email,''),deletion.confirmation_code_hash),'status':deletion.status,'attempts_left':deletion.confirmation_attempts_left,'active':deletion.user.is_active})
 proof={'read_only':True,'requests':rows,'matched_mail_recipients':len(messages),'mail_contents_codes_tokens_saved_in_artifacts':False}
 (HERE/'readback-final.json').write_text(json.dumps(proof,indent=2));assert len(rows)==18 and all(r['local_mail_code_matches_own_request']and r['active']and r['status']=='CONFIRMATION_SENT'and r['attempts_left']==4 for r in rows)
 print('18 own letters linked to correct recipients and DB code hashes;18active pending requests,4attempts each;read-only')
else:raise SystemExit('Unknown mode')
