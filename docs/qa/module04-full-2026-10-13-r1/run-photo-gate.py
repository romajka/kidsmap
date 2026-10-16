from pathlib import Path
import sys
from django.conf import settings
from django.core.management import call_command
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
settings.SESSION_COOKIE_NAME='sessionid';settings.CSRF_COOKIE_NAME='csrftoken'
settings.MEDIA_ROOT=settings.QA_ROOT/'gate-unit-media';settings.PRIVATE_MEDIA_ROOT=settings.QA_ROOT/'gate-unit-private-media'
settings.CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':settings.QA_ROOT.name+'-gate-unit'}}
call_command('test','event_photo_gate.EventPhotoGateTests',interactive=False,verbosity=1)
