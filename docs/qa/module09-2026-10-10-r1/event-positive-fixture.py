import sys,json
sys.argv=['run.py','qa-fixture'];from run import *
from catalog.models import *
from catalog.services.review_versions import submit_review,moderate_candidate
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
f=json.loads((HERE/'fixtures.json').read_text());e=json.loads((HERE/'extra-fixtures.json').read_text());U=get_user_model();owner=U.objects.get(pk=f['actors']['owner']['id'])
assert not Event.objects.filter(name='Fictional QA09 valid organizer').exists()
event=Event.objects.create(name='Fictional QA09 valid organizer',name_az='Uydurma QA09 təsdiqlənmiş tədbir',owner=owner,organizer_specialist_id=e['specialist'],organizer_resolution='resolved',category=Place.objects.get(pk=f['places']['live']).category,status='published',event_format='online',start_datetime=timezone.now()+timedelta(days=7),end_datetime=timezone.now()+timedelta(days=7,hours=1),description_az='Uydurma tədbir. '*25)
h,v=submit_review(target=event,user=U.objects.get(pk=f['actors']['author']['id']),rating=5,text='QA09 INITIAL VALID ORGANIZER REVIEW',author_name='Fictional Author');moderate_candidate(head=h,revision_id=v.pk,actor=U.objects.get(pk=f['actors']['admin']['id']),approve=True)
e['event']=event.pk;(HERE/'extra-fixtures.json').write_text(json.dumps(e,indent=2));print('New valid-organizer event initial case')
