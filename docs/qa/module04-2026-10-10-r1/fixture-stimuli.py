"""Explicit SIMULATED concurrent organizer/venue fixture changes, never Event writes."""
import sys,json,datetime
action=sys.argv[1];sys.argv=['run.py','qa-fixture']
from run import *
from catalog.models import Organization,Place
f=json.loads((HERE/'fixtures.json').read_text())
assert settings.TESTING and settings.DATABASES['default']['NAME']=='module04'
if action=='revoke':Organization.objects.filter(pk=f['organization'],owner_id=f['actors']['owner']).update(owner_id=f['actors']['outsider'])
elif action=='restore':Organization.objects.filter(pk=f['organization']).update(owner_id=f['actors']['owner']);Place.objects.filter(pk=f['venues']['public']).update(is_active=True)
elif action=='hide-venue':Place.objects.filter(pk=f['venues']['public']).update(is_active=False)
else:raise RuntimeError('Unknown own fixture action')
with (HERE/'fixture-stimuli.jsonl').open('a',encoding='utf-8') as out:out.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':action,'simulated_fixture_only':True,'event_writes':0})+'\n')
print('Own fixture-only stimulus:',action)
