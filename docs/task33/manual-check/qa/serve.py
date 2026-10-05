from pathlib import Path
import json,os,sys
import django
from django.conf import settings
from guard import validate_settings,install_network_guard,install_libpq_guard

validate_settings(settings)
install_network_guard();install_libpq_guard();django.setup()
from django.core.management import call_command
call_command('migrate',interactive=False,verbosity=0)
from seed import seed
seed()
portable=os.environ.get('KIDSMAP_MANUAL_PORTABLE')=='1'
port=int(os.environ.get('KIDSMAP_PREVIEW_PORT','8780')) if portable else 8780
if portable:
    from add_demo_places import main as add_places
    sys.argv=[sys.argv[0],'--apply']
    add_places()
call_command('check',verbosity=0)
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.servers.basehttp import ThreadedWSGIServer,WSGIRequestHandler
server=ThreadedWSGIServer(('127.0.0.1',port),WSGIRequestHandler,allow_reuse_address=True)
server.set_app(StaticFilesHandler(get_wsgi_application()))
print(f'READY http://localhost:{port}/qa/ — full Django application, synthetic data only',flush=True)
server.serve_forever()
