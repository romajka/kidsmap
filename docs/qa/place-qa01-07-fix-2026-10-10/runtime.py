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
os.environ.update(DJANGO_TESTING='1', DJANGO_DEBUG='1', DJANGO_SETTINGS_MODULE='kmfix_settings',
                  PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
sys.path[:0] = [str(HERE), str(ROOT / 'src')]
connect = socket.socket.connect


def isolated_connect(sock, address):
    if not isinstance(address, tuple) or address[0] not in ('127.0.0.1','localhost') or address[1] != 55445:
        raise RuntimeError('Only the dedicated QA PostgreSQL connection is allowed')
    return connect(sock, address)


socket.socket.connect = isolated_connect
import importlib.util
spec=importlib.util.spec_from_file_location('isolated_locales',ROOT/'scripts/build_isolated_locales.py')
locale_builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(locale_builder)
manifest=locale_builder.verify(ROOT/'.tmp/place-qa01-07-fix-20261010/locale-build-02/manifest.json',ROOT/'locale')
assert manifest['locales']==['ru','az','en']
if sys.argv[1]=='preflight':
    print('Locale preflight passed before Django.setup; no DB or HTTP connection opened.')
    raise SystemExit(0)
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
assert settings.TESTING and settings.DATABASES['default']['NAME'] == 'placekmfix_plan'
for directory in (settings.MEDIA_ROOT, settings.PRIVATE_MEDIA_ROOT):
    Path(directory).mkdir(parents=True, exist_ok=True)

if sys.argv[1] == 'prepare':
    call_command('migrate', interactive=False, verbosity=0)
    from django.contrib.auth import get_user_model
    from django.test import Client
    from catalog.models import Category, Place
    actor = get_user_model().objects.create_user('kmfix_synthetic_owner', 'kmfix@example.invalid', secrets.token_urlsafe(32))
    category, _ = Category.objects.get_or_create(code='EDU', defaults={'name':'Education'})
    place = Place.objects.create(name='KMFIX synthetic place', name_ru='KMFIX Вымышленное место',
        name_az='KMFIX Uydurma məkan', name_en='KMFIX Synthetic place', category=category,
        owner=actor, created_by=actor, status='draft', is_active=False, lat=40.4093, lng=49.8671)
    client = Client()
    client.force_login(actor)
    state = {'cookies':[{'name':settings.SESSION_COOKIE_NAME,'value':client.cookies[settings.SESSION_COOKIE_NAME].value,
        'domain':'127.0.0.1','path':'/','httpOnly':True,'secure':False,'sameSite':'Lax'}], 'origins':[]}
    (settings.QA_ROOT / 'browser-state.json').write_text(json.dumps(state), encoding='utf-8')
    metadata = {'DJANGO_TESTING':True, 'database':'placekmfix_plan', 'database_port':55445,
        'url':f'http://127.0.0.1:8840/ru/account/places/{place.pk}/edit/',
        'django':django.get_version(),'python':sys.version.split()[0], 'records':'synthetic only',
        'environment_allowlisted':True,'external_transport_blocked':True,
        'cache':settings.CACHES['default']['BACKEND'],'email':settings.EMAIL_BACKEND,
        'locale_paths':[str(p) for p in settings.LOCALE_PATHS],'compiled_assets':'frozen baseline copies, not recompiled','media_root':str(settings.MEDIA_ROOT),'private_media_root':str(settings.PRIVATE_MEDIA_ROOT)}
    (HERE / 'isolation.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
    print('Prepared isolated synthetic owner/place; browser state stored only in ignored scratch.')
elif sys.argv[1] == 'serve':
    (HERE / 'server-process.json').write_text(json.dumps({'pid':os.getpid(),'script':str(Path(__file__).resolve()),'mode':'serve'})+'\n', encoding='utf-8')
    call_command('runserver', '127.0.0.1:8840', use_reloader=False, use_threading=True, verbosity=0)
elif sys.argv[1] == 'test':
    call_command('test',*sys.argv[2:],interactive=False,verbosity=1)
elif sys.argv[1] == 'script':
    import runpy
    runpy.run_path(str(HERE / sys.argv[2]),init_globals={'settings':settings},run_name='__main__')
elif sys.argv[1] == 'checks':
    call_command('test',
        'catalog.testcases.test_task33_place_continuous.ContinuousPlaceFormTests.test_edit_displays_candidate_nature_and_saved_gallery_without_changing_live',
        'catalog.testcases.test_task33_place_continuous.ContinuousPlaceFormTests.test_public_space_can_submit_without_organization_photo_coordinates_or_contact',
        interactive=False, verbosity=1)
else:
    raise SystemExit('Use prepare, serve or checks')
