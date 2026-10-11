"""Isolated QA-only runtime, synthetic records and loopback server."""
import json
import os
import secrets
import socket
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for name in list(os.environ):
    if name.upper() not in {'SYSTEMROOT','WINDIR','TEMP','TMP','PATH','PATHEXT','COMSPEC'}:
        os.environ.pop(name)
os.environ.update(DJANGO_TESTING='1', DJANGO_DEBUG='1', DJANGO_SETTINGS_MODULE='qa05_settings',
                  PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
sys.path[:0] = [str(HERE), str(ROOT / 'src')]
connect = socket.socket.connect


def isolated_connect(sock, address):
    if not isinstance(address, tuple) or address[0] not in ('127.0.0.1','localhost') or address[1] != 55440:
        raise RuntimeError('Only the dedicated QA PostgreSQL connection is allowed')
    return connect(sock, address)


socket.socket.connect = isolated_connect
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
assert settings.TESTING and settings.DATABASES['default']['NAME'] == 'placeqa05_plan'
for directory in (settings.MEDIA_ROOT, settings.PRIVATE_MEDIA_ROOT):
    Path(directory).mkdir(parents=True, exist_ok=True)

if sys.argv[1] == 'prepare':
    call_command('migrate', interactive=False, verbosity=0)
    from django.contrib.auth import get_user_model
    from django.test import Client
    from catalog.models import Category, Place
    actor = get_user_model().objects.create_superuser('qa05_synthetic_admin', 'qa05@example.invalid', secrets.token_urlsafe(32))
    category, _ = Category.objects.get_or_create(code='EDU', defaults={'name':'Education'})
    Category.objects.create(code='QA05_LONG', name='QA05 synthetic long category',
        name_ru='QA05 Вымышленная категория для проверки длинного названия образовательных и творческих занятий',
        name_az='QA05 Uzun kateqoriya adının yoxlanılması üçün uydurma təhsil və yaradıcılıq məşğələləri',
        name_en='QA05 Synthetic category for testing a long educational and creative activities label')
    place = Place.objects.create(name='QA05 synthetic place', name_ru='QA05 Вымышленное место',
        name_az='QA05 Uydurma məkan', name_en='QA05 Synthetic place', category=category,
        status='draft', is_active=False, lat=40.4093, lng=49.8671)
    client = Client()
    client.force_login(actor)
    state = {'cookies':[{'name':settings.SESSION_COOKIE_NAME,'value':client.cookies[settings.SESSION_COOKIE_NAME].value,
        'domain':'127.0.0.1','path':'/','httpOnly':True,'secure':False,'sameSite':'Lax'}], 'origins':[]}
    (settings.QA_ROOT / 'browser-state.json').write_text(json.dumps(state), encoding='utf-8')
    metadata = {'DJANGO_TESTING':True, 'database':'placeqa05_plan', 'database_port':55440,
        'url':f'http://127.0.0.1:8819/admin/catalog/place/{place.pk}/change/',
        'django':django.get_version(),'python':sys.version.split()[0], 'records':'synthetic only',
        'environment_allowlisted':True,'external_transport_blocked':True,
        'cache':settings.CACHES['default']['BACKEND'],'email':settings.EMAIL_BACKEND,
        'media_root':str(settings.MEDIA_ROOT),'private_media_root':str(settings.PRIVATE_MEDIA_ROOT)}
    (HERE / 'isolation.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
    print('Prepared isolated synthetic admin/place; browser state stored only in ignored scratch.')
elif sys.argv[1] == 'serve':
    (HERE / 'server-process.json').write_text(json.dumps({'pid':os.getpid(),'script':str(Path(__file__).resolve()),'mode':'serve'})+'\n', encoding='utf-8')
    call_command('runserver', '127.0.0.1:8819', use_reloader=False, use_threading=True, verbosity=0)
else:
    raise SystemExit('Use prepare or serve')
