"""Own loopback-only runtime attestation. No database or application actions."""
import hashlib
import json
import os
import sys
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse
from django.urls import path
from django.db import connection, transaction
from config.urls import urlpatterns as application

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def source_hashes():
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for p in (ROOT/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
START=source_hashes()
def version(request):
    assert settings.TESTING and request.META['REMOTE_ADDR'] in ('127.0.0.1','::1')
    snap=json.loads((HERE/'runtime-snapshot.json').read_text(encoding='utf-8'))
    current=source_hashes()
    return JsonResponse({'head':snap['head'],'branch':snap['branch'],'snapshot_matches_startup':snap['source_files']==START,'startup_matches_disk':START==current,'startup_digest':hashlib.sha256(json.dumps(START,sort_keys=True).encode()).hexdigest(),'disk_digest':hashlib.sha256(json.dumps(current,sort_keys=True).encode()).hexdigest(),'testing':settings.TESTING,'debug':settings.DEBUG,'db':'qa08_district','db_port':55447,'pid':os.getpid(),'python':sys.version.split()[0],'django':__import__('django').get_version(),'locale_profile':settings.LOCALE_PROFILE,'locale_paths':list(settings.LOCALE_PATHS)})
def state(request):
    assert settings.TESTING and request.META['REMOTE_ADDR'] in ('127.0.0.1','::1')
    from catalog.models import Place, VolunteerPlaceRevision
    fixtures=json.loads((HERE/'fixtures.json').read_text(encoding='utf-8'))
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION READ ONLY')
            cursor.execute("SET LOCAL statement_timeout='10s'")
            cursor.execute("SET LOCAL lock_timeout='2s'")
        place=Place.objects.get(pk=fixtures['place'])
        revision=VolunteerPlaceRevision.objects.filter(place=place).first()
        payload=revision.payload if revision else {}
        live={k:getattr(place,k) for k in ('district','address','status','name_az','name_ru','name_en','nature')}
        return JsonResponse({'live':live,'revision_exists':revision is not None,'candidate_payload_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest(),'candidate_effective_district':payload.get('district',place.district),'candidate_effective_address':payload.get('address',place.address),'revision_version':revision.version if revision else 0})
urlpatterns=[path('qa/version/',version),path('qa/state/',state)]+application
