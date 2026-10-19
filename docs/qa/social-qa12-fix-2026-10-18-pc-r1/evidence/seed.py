import sys,json
sys.argv=['runtime.py','fixture-seed'];from runtime import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from catalog.models import Specialist,Activity,Event
from catalog.testcases.utils import create_ready_place
from catalog.services.review_versions import submit_review,moderate_candidate
U=get_user_model();assert settings.TESTING and settings.DATABASES['default']['NAME']=='m09full_r1' and not U.objects.filter(username__startswith='qa12fix_').exists()
author=U.objects.create_user('qa12fix_author',email='s12-author@example.invalid',first_name='Fictional S12 Author');voter=U.objects.create_user('qa12fix_voter',email='s12-voter@example.invalid',first_name='Fictional S12 Voter');moderator=U.objects.get(username='qa09_admin')
place=create_ready_place(name='Fictional S12 place',name_az='Uydurma S12 məkan',name_ru='Вымышленное S12 место',name_en='Fictional S12 place',owner=moderator,created_by=moderator,status='published',is_active=True)
spec=Specialist.objects.create(name='Fictional S12 specialist',status='published',is_active=True)
activity=Activity.objects.create(place=place,status='published',name_az='Uydurma S12 fəaliyyət')
event=Event.objects.create(name='Fictional S12 event',name_az='Uydurma S12 tədbir',organizer_specialist=spec,organizer_resolution='resolved',category=place.category,status='published',event_format='online',start_datetime=timezone.now()+timedelta(days=5),end_datetime=timezone.now()+timedelta(days=5,hours=1))
cases={}
for kind,target in [('place',place),('activity',activity),('specialist',spec),('event',event)]:
 h,old=submit_review(target=target,user=author,rating=4,text='QA12 OLD '+kind,author_name='Fictional S12 Author');moderate_candidate(head=h,revision_id=old.pk,actor=moderator,approve=True)
 h,new=submit_review(target=target,user=author,rating=5,text='QA12 NEW '+kind,author_name='Fictional S12 Author',expected_revision_id=old.pk)
 cases[kind]={'target_id':target.pk,'head_id':h.pk,'old_revision':old.pk,'new_revision':new.pk,'old_text':'QA12 OLD '+kind,'new_text':'QA12 NEW '+kind}
(QA/'fixtures.json').write_text(json.dumps({'synthetic_only':True,'author_id':author.pk,'voter_id':voter.pk,'cases':cases},indent=2));print(json.dumps({'owned_fictional_users':2,'targets':4,'review_heads':4,'revisions':8}))
