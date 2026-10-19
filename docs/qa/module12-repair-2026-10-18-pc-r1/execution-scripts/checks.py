import sys,json,io
sys.argv=['runtime.py','checks'];from runtime import *
from django.core.management import call_command
out=io.StringIO();call_command('check',stdout=out);call_command('makemigrations',check=True,dry_run=True,verbosity=1,stdout=out)
(QA/'checks-result.json').write_text(json.dumps({'exit':0,'commands':['check','makemigrations --check --dry-run'],'safe_summary':[s for s in out.getvalue().splitlines() if s.startswith(('System check','No changes detected'))],'source_RO':True,'own_DB':True},indent=2));print('Django check and migration drift check passed on own isolated profile.')
