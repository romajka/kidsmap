"""Read-only reuse of this same execution's verified, isolated SOCIAL01 fix profile."""
import hashlib,importlib.util,json,os,socket,subprocess,sys,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];FIX=H.parent/'social-qa01-fix-2026-10-16-r1';S=R/'.tmp'/FIX.name
cfg=json.loads((S/'config.json').read_text());meta=json.loads((FIX/'server-current.json').read_text());expected=json.loads((FIX/'runtime-source-green-tests.json').read_text())
source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=10));assert source['source']==expected and source['startup_matches_disk']and source['pid']==meta['pid'];assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in expected.items())
label=subprocess.check_output(['docker','inspect','--format','{{index .Config.Labels "kidsmap.qa.run"}}',cfg['container']],text=True).strip();assert label==FIX.name
assert source['sole_locale_paths']==[str(S/'locales/locale')]
spec=importlib.util.spec_from_file_location('isolated_builder',R/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);manifest=builder.verify(S/'locales/manifest.json',R/'locale');assert manifest['locales']==['ru','az','en']
for k in list(os.environ):
 if k not in {'PATH','LANG','LC_ALL','TZ'}:os.environ.pop(k)
os.environ.update(DJANGO_TESTING='1',DJANGO_DEBUG='1',DJANGO_SETTINGS_MODULE='settings',PYTHONDONTWRITEBYTECODE='1');sys.dont_write_bytecode=True;sys.path[:0]=[str(FIX),str(R/'src'),str(S/'python-deps')]
_connect=socket.socket.connect;_connect_ex=socket.socket.connect_ex
def allowed(addr):return isinstance(addr,tuple)and len(addr)>=2 and addr[0]in('127.0.0.1','localhost')and addr[1]==cfg['pg_port']
def connect(sock,addr):
 if not allowed(addr):raise RuntimeError('QA02 egress denied')
 return _connect(sock,addr)
def connect_ex(sock,addr):
 if not allowed(addr):raise RuntimeError('QA02 egress denied')
 return _connect_ex(sock,addr)
socket.socket.connect=connect;socket.socket.connect_ex=connect_ex
import django
django.setup()
from django.conf import settings
from django.db import transaction,connection
from catalog.services.review_versions import review_types,rating_summary
assert settings.TESTING and settings.QA_ROOT==S and tuple(settings.LOCALE_PATHS)==(manifest['locale_root'],)and settings.DATABASES['default']['NAME']==cfg['database']
fixture=json.loads((FIX/'fixtures.json').read_text());case=fixture['cases'][0];rows=[]
with transaction.atomic():
 with connection.cursor()as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
 for kind,types in review_types().items():
  for scenario,role in [('rejected-edit','author'),('rejected-first','rejected')]:
   head=types[1].objects.get(**{kind+'_id':case['targets'][kind],'user_id':case['actors'][role]['id'],'is_current':True});rev=head.revisions.order_by('-created_at','-pk').first();assert rev.status=='rejected'
   reason=rev.rejection_reason;assert reason=='Fictional rejection for rating readback'
   rows.append({'kind':kind,'scenario':scenario,'author_id':head.user_id,'head_id':head.pk,'latest_revision_id':rev.pk,'latest_status':rev.status,'latest_rating':rev.rating,'current_id':head.current_revision_id,'candidate_id':head.candidate_revision_id,'reason_is_fixture':True,'reason_sha256':hashlib.sha256(reason.encode()).hexdigest(),'rejected_text_sha256':hashlib.sha256(rev.text.encode()).hexdigest(),'public_summary':rating_summary(types[0].objects.get(pk=case['targets'][kind]))})
result={'rows':rows,'read_only':True,'source_files':len(expected),'source_match':True,'profile':str(S),'profile_owner_label_verified':True,'locales_verified':True,'sole_locale_paths':source['sole_locale_paths'],'testing':settings.TESTING,'database':cfg['database'],'cache':settings.CACHES['default'],'media':str(settings.MEDIA_ROOT),'private_media':str(settings.PRIVATE_MEDIA_ROOT),'email_backend':settings.EMAIL_BACKEND,'source_pid':source['pid'],'reuse_reason':'same execution-owned current profile; native submit/reject transitions from SOCIAL01 fix retained by exact source hashes; this run performs fresh readback and UI reload only'}
(H/'readback.json').write_text(json.dumps(result,indent=2));(H/'runtime-source.json').write_text(json.dumps(source,indent=2));print(json.dumps({'rows':len(rows),'read_only':True,'source_match':len(expected),'profile_owner_verified':True,'locales_verified':True}))
