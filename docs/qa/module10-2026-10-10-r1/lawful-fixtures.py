"""Additional INITIAL lawful person/organizer cases; audited OFF/ON remains native."""
import sys,json
sys.argv=['run.py','qa-fixture'];from run import *
from catalog.models import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
f=json.loads((HERE/'fixtures.json').read_text());U=get_user_model();owner=U.objects.get(pk=f['actors']['owner']['id'])
assert not (HERE/'lawful-fixtures.json').exists()
s=Specialist.objects.create(name='Fictional QA10 lawful person',name_alt='Uydurma QA10 şəxs',owner=owner,created_by=owner,verified_person_user=owner,person_verified_at=timezone.now(),status='published',is_active=True,bio_az='Uydurma şəxs. '*25)
e=Event.objects.create(name='Fictional QA10 lawful event',name_az='Uydurma QA10 təşkilatçı tədbiri',owner=owner,organizer_specialist=s,organizer_resolution='resolved',category=Place.objects.get(pk=f['places']['live']).category,status='published',event_format='online',start_datetime=timezone.now()+timedelta(days=7),end_datetime=timezone.now()+timedelta(days=7,hours=1),description_az='Uydurma tədbir. '*25)
(HERE/'lawful-fixtures.json').write_text(json.dumps({'specialist':s.pk,'event':e.pk,'initial_only':True},indent=2))
print('New lawful synthetic person and organizer cases',s.pk,e.pk)
