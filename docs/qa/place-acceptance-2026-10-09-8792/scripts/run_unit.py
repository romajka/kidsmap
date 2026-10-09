import os,sys,json,runpy
from pathlib import Path
S=Path(__file__).resolve().parent;R=S.parents[1];env=json.loads((S/'env.json').read_text());os.environ.clear();os.environ.update(env);sys.path[:0]=env['PYTHONPATH'].split(os.pathsep)
from django.conf import settings
from guard import validate_settings,install_network_guard,install_libpq_guard
validate_settings(settings);install_network_guard();install_libpq_guard()
import django;django.setup()
from django.core.management import call_command
if sys.argv[1]=='--script':runpy.run_path(str(S/sys.argv[2]),run_name='__main__')
else:call_command('test',*sys.argv[1:],interactive=False,verbosity=1,keepdb=False)
