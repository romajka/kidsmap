"""Discard only incomplete own initial fixtures before any audited transitions."""
import sys
sys.argv=['run.py','qa-bootstrap-retry'];from run import *
assert not (HERE/'fixtures.json').exists()
from django.db.migrations.recorder import MigrationRecorder
assert MigrationRecorder.Migration.objects.count()==175
call_command('flush',interactive=False,verbosity=0)
import seed
