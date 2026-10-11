"""Fresh isolated QA launcher. No inherited credentials or checkout .env."""
import os, sys, json, hashlib, subprocess, socket, secrets
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STATE = ROOT / '.tmp/module01-20261009-r1'
for name in list(os.environ):
    if name.startswith(('DJANGO_', 'DATABASE_', 'LEGACY_', 'REDIS_', 'GOOGLE_', 'EMAIL_', 'INDEXNOW_', 'TASK33_')):
        os.environ.pop(name)
os.environ.update(DJANGO_TESTING='1', DJANGO_DEBUG='1', DJANGO_SETTINGS_MODULE='qa_settings', PYTHONDONTWRITEBYTECODE='1')
sys.path[:0] = [str(HERE), str(ROOT / 'src')]
STATE.mkdir(parents=True, exist_ok=True)
for name in ('media', 'private-media', 'assets'):
    (STATE / name).mkdir(exist_ok=True)
real_connect = socket.socket.connect
def guarded_connect(sock, address):
    if isinstance(address, tuple) and address[0] not in ('127.0.0.1', 'localhost', '::1'):
        raise RuntimeError('External network blocked by QA launcher')
    return real_connect(sock, address)
socket.socket.connect = guarded_connect
import django
django.setup()
from django.core.management import call_command
from django.conf import settings
assert settings.TESTING and settings.DATABASES['default']['NAME'] == 'module01'
assert settings.DATABASES['default']['PORT'] == '55431'
mode = sys.argv[1]
if mode == 'snapshot':
    source = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for top in ('src', 'static', 'config', 'locale') for p in (ROOT / top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    x = {'checkout': str(ROOT), 'head': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT,text=True).strip(), 'branch': subprocess.check_output(['git','branch','--show-current'], cwd=ROOT,text=True).strip(), 'entry_worktree': [], 'active_run': 'NONE', 'source_files': source, 'source_digest': hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()}
    (HERE / 'snapshot.json').write_text(json.dumps(x,indent=2),encoding='utf-8')
    print('Snapshot files',len(source))
elif mode == 'migrate':
    call_command('migrate', interactive=False, verbosity=1)
elif mode == 'serve':
    x=json.loads((HERE/'snapshot.json').read_text())
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in x['source_files'].items())
    from catalog.services import publication_forms,publication
    from django.core import signing
    original_source_version=publication_forms.source_version
    def source_diagnostic(form,place):
        try:
            d=signing.loads(form.data.get('publication_token',''),salt='publication-source')
            current=publication.snapshot(place,'place')
            record={'place_id':place.pk,'source_matches':d['source']==place.content_version,'snapshot_mismatch_keys':[k for k in current if current[k]!=d['snapshot'].get(k)],'dependencies_match':d['dependencies']==publication.dependencies(place,'place')}
            with (HERE/'source-diagnostics.jsonl').open('a',encoding='utf-8') as out:out.write(json.dumps(record)+'\n')
        except signing.BadSignature:pass
        return original_source_version(form,place)
    publication_forms.source_version=source_diagnostic
    call_command('runserver','127.0.0.1:8811',use_reloader=False)
elif mode == 'test':
    settings.MEDIA_ROOT=STATE/'unit-media'
    settings.PRIVATE_MEDIA_ROOT=STATE/'unit-private-media'
    call_command('test', *sys.argv[2:], interactive=False, verbosity=1)
elif mode == 'seed':
    from django.contrib.auth import get_user_model
    from catalog.models import Category, Subcategory
    from PIL import Image
    credential=secrets.token_hex(16)
    (STATE/'credential').write_text(credential)
    for role in ('owner','outsider','moderator'):
        u=get_user_model().objects.create_user('qa_'+role, email=role+'@example.invalid',password=credential)
        if role=='moderator':
            u.is_staff=u.is_superuser=True;u.save()
    for code, title in [('EDU','Təhsil'),('FUN','Əyləncə')]:
        c,_=Category.objects.get_or_create(code=code,defaults={'name':title})
    print('taxonomy fields', [f.name for f in Subcategory._meta.fields])
    Image.new('RGB',(1000,750),'#81b8a2').save(STATE/'assets/cover.png')
    Image.new('RGB',(1000,750),'#dbb876').save(STATE/'assets/gallery.png')
    (STATE/'assets/invalid.txt').write_text('synthetic non-image')
    print('Synthetic actors/images created')
elif mode == 'fixture-org':
    from catalog.models import Organization
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    org=Organization.objects.create(name_az='QA fictional network',owner=get_user_model().objects.get(username='qa_owner'),status='published',approved_at=timezone.now())
    print('Synthetic organization fixture',org.pk)
elif mode == 'observe':
    from catalog.models import Place,VolunteerPlaceRevision
    print(json.dumps({'places':list(Place.objects.values('id','status','name_az','name_ru','name_en','organization_id','content_version','lat','lng','address')), 'revisions':list(VolunteerPlaceRevision.objects.filter(place__isnull=False).values('place_id','status','review_note','version','changed_fields'))},default=str,ensure_ascii=True))
elif mode == 'fixture-images':
    from PIL import Image
    Image.new('RGB',(1000,750),'#a5bfe5').save(STATE/'assets/gallery-two.png')
    (STATE/'assets/corrupt.png').write_bytes(b'not a png')
    (STATE/'assets/empty.png').write_bytes(b'')
    (STATE/'assets/oversize.png').write_bytes(b'0'*(16*1024*1024))
elif mode == 'fixture-password':
    from django.contrib.auth import get_user_model
    credential=secrets.token_hex(16)
    (STATE/'credential').write_text(credential)
    for u in get_user_model().objects.filter(username__in=['qa_owner','qa_outsider','qa_moderator']):
        u.set_password(credential);u.save(update_fields=['password'])
    print('Synthetic credentials rotated; stored only in ignored scratch')
