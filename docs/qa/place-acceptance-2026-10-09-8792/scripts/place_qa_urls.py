from manual_urls import urlpatterns as original
from django.urls import path
from django.http import JsonResponse
from django.conf import settings
from pathlib import Path
import json

def version(request):
 x=json.loads(Path(__file__).with_name('runtime-source.json').read_text())
 return JsonResponse({'head':x['head'],'source_digest':x['source_digest'],'files':len(x['source_files']),'testing':settings.TESTING,'external_credentials_present':any(getattr(settings,k,'') for k in ('GOOGLE_MAPS_API_KEY','GOOGLE_OAUTH_CLIENT_SECRET','GOOGLE_ANALYTICS_MEASUREMENT_ID')),'cache':settings.CACHES['default']['BACKEND'],'email':settings.EMAIL_BACKEND,'media_isolated':str(settings.MEDIA_ROOT).startswith('/tmp/kidsmap-task33-qa04-place-acceptance'),'private_media_isolated':str(settings.PRIVATE_MEDIA_ROOT).startswith('/tmp/kidsmap-task33-qa04-place-acceptance'),'started_at':settings.ACCEPTANCE_STARTED_AT})
urlpatterns=[path('qa/acceptance-version/',version)]+original
