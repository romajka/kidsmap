from pathlib import Path
import json
import django
from django.conf import settings
from guard import validate_settings,install_network_guard,install_libpq_guard

validate_settings(settings)
install_network_guard();install_libpq_guard();django.setup()
from django.core.management import call_command
call_command('migrate',interactive=False,verbosity=0)
from seed import seed
seed()
call_command('check',verbosity=0)
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.servers.basehttp import ThreadedWSGIServer,WSGIRequestHandler
server=ThreadedWSGIServer(('127.0.0.1',8780),WSGIRequestHandler,allow_reuse_address=True)
server.set_app(StaticFilesHandler(get_wsgi_application()))
print('READY http://localhost:8780/qa/ — full Django application, synthetic data only',flush=True)
server.serve_forever()
