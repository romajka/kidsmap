import json
from pathlib import Path
from django.urls import path
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from config.urls import urlpatterns as application
def version(request):
    data = json.loads((Path(__file__).parent / 'snapshot.json').read_text())
    return JsonResponse({'head': data['head'], 'source_digest': data['source_digest'], 'testing': settings.TESTING, 'database': 'isolated-postgresql-module07', 'cache': settings.CACHES['default']['BACKEND'], 'email': settings.EMAIL_BACKEND})
from qa_evidence import mail,state
urlpatterns = [path('qa/version/', version),path('qa/mail/',mail),path('qa/state/',state)] + application
