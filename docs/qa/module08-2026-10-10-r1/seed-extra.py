"""Add NEW valid initial fixtures only; never alter audited existing objects."""
import sys,json
sys.argv=['run.py','qa-extra-fixtures'];from run import *
from catalog.models import Event,Organization
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
assert not (HERE/'extra-fixtures.json').exists()
assert Event.objects.count()==1
owner=get_user_model().objects.get(username='qa08_owner')
org=Organization.objects.create(owner=owner,created_by=owner,name_az='Uydurma QA08 valid initial organizer',status='published',description_az='Synthetic initial organizer with active fictional owner')
event=Event.objects.create(name='Fictional QA08 valid initial event',name_az='Uydurma QA08 valid initial event',name_ru='Synthetic QA08 valid event RU',name_en='Fictional QA08 valid event EN',category='EDU',organizer_organization=org,organizer_resolution='resolved',owner=owner,status='pending',event_format='online',start_datetime=timezone.now()+timedelta(days=4),end_datetime=timezone.now()+timedelta(days=4,hours=2),description_az='Synthetic valid initial event. '*30,phone='+994500000008',photo='places/qa08-live.png')
x={'new_initial_only':True,'event':event.pk,'organization':org.pk,'reason':'Earlier event fixture had organizer.owner=NULL and no photo. Domain correctly rejects organizer; no existing audited fixture changed.'}
(HERE/'extra-fixtures.json').write_text(json.dumps(x,indent=2),encoding='utf-8');print(json.dumps(x))
