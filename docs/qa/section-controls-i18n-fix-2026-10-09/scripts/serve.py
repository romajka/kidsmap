from pathlib import Path
import datetime,hashlib,json,os,sys
from django.conf import settings
from guard import validate_settings,install_network_guard,install_libpq_guard
root=Path('/home/ramin/kidsmap');scratch=Path(__file__).parent
snapshot=json.loads((scratch/'runtime-source.json').read_text())
for path,digest in {**snapshot['source_files']}.items():
    if hashlib.sha256((root/path).read_bytes()).hexdigest()!=digest:raise RuntimeError('Source drift before startup: '+path)
validate_settings(settings);install_network_guard();install_libpq_guard()
settings.ACCEPTANCE_STARTED_AT=datetime.datetime.now(datetime.timezone.utc).isoformat()
import django;django.setup()
from django.core.management import call_command
call_command('check',verbosity=0)
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.servers.basehttp import ThreadedWSGIServer,WSGIRequestHandler
server=ThreadedWSGIServer(('127.0.0.1',8792),WSGIRequestHandler,allow_reuse_address=True)
server.set_app(StaticFilesHandler(get_wsgi_application()))
print('READY http://localhost:8792/qa/ digest '+snapshot['source_digest'],flush=True)
server.serve_forever()
