import os,sys,runpy
from pathlib import Path
ROOT=Path('/home/ramin/kidsmap');SCRATCH=Path(__file__).parent
STATE=Path('/tmp/kidsmap-task33-qa04-place-form-implementation-20261007')
os.environ.clear();os.environ.update(PATH='/usr/bin:/bin:/snap/bin',LANG='C.UTF-8',PYTHONDONTWRITEBYTECODE='1',DJANGO_TESTING='1',DJANGO_SETTINGS_MODULE='acceptance_settings',DJANGO_SECRET_KEY='content-acceptance-synthetic-only',DATABASE_URL='',LEGACY_DATABASE_URL='',REDIS_URL='',TASK33_QA_ROOT=str(STATE),TASK33_QA_SOCKET=str(ROOT/'.tmp/kidsmap-task33-qa04-socket-place-form-implementation-20261007'),TASK33_QA_OUTPUT=str(STATE),KIDSMAP_MANUAL_PORTABLE='1',KIDSMAP_PREVIEW_PORT='8784')
sys.path[:0]=[str(SCRATCH),str(ROOT/'docs/task33/manual-check/qa'),str(ROOT/'docs/task33/qa04'),str(ROOT/'src')]
from django.conf import settings
from guard import validate_settings,install_network_guard,install_libpq_guard
validate_settings(settings);install_network_guard();install_libpq_guard()
import django;django.setup()
from django.core.management import call_command
if sys.argv[1]=='--script':
    path=(SCRATCH/sys.argv[2]).resolve()
    assert path.is_relative_to(SCRATCH)
    runpy.run_path(str(path),run_name='__main__')
else:call_command('test',*sys.argv[1:],interactive=False,verbosity=2,keepdb=False)
