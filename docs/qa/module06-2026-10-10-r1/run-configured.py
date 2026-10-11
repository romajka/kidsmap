"""Own companion process: simulate configured map transport, no external key."""
import sys
sys.argv=['run.py','qa-configured'];from run import *
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in json.loads((HERE/'snapshot.json').read_text())['source_files'].items())
settings.GOOGLE_MAPS_API_KEY='QA_LOCAL_ADAPTER_NOT_A_VALID_KEY'
settings.PUBLIC_BASE_URL='http://localhost:8818'
settings.CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'module06-r1-configured'}}
settings.SESSION_COOKIE_NAME='module06_sdk_session';settings.CSRF_COOKIE_NAME='module06_sdk_csrf'
call_command('runserver','127.0.0.1:8818',use_reloader=False)
