import json
from pathlib import Path
from django.http import JsonResponse
from django.urls import path
from manual_urls import urlpatterns as original
from django.conf import settings
def version(request):
    snapshot=json.loads((Path(__file__).parent/'runtime-source.json').read_text())
    return JsonResponse({'head':snapshot['head'],'source_digest':snapshot['source_digest'],'worktree_entries':len(snapshot['worktree_status']),
      'DJANGO_TESTING':settings.TESTING,'external_credentials_present':any(getattr(settings,k,'') for k in ['GOOGLE_MAPS_API_KEY','GOOGLE_OAUTH_CLIENT_SECRET','GOOGLE_ANALYTICS_MEASUREMENT_ID']),
      'locmem_cache':settings.CACHES['default']['BACKEND'].endswith('LocMemCache'),'locmem_email':settings.EMAIL_BACKEND.endswith('locmem.EmailBackend'),
      'public_base_url':settings.PUBLIC_BASE_URL,'started_at':getattr(settings,'ACCEPTANCE_STARTED_AT',None)})
urlpatterns=[path('qa/acceptance-version/',version)]+original
