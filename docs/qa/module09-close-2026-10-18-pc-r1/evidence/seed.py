import sys,json
sys.argv=['runtime.py','fixture-seed'];from runtime import *
from django.contrib.auth import get_user_model
from catalog.models import Specialist
from catalog.testcases.utils import create_ready_place
from catalog.services.review_versions import submit_review,moderate_candidate
assert settings.TESTING and settings.DATABASES['default']['NAME']=='m09full_r1'
U=get_user_model();assert not U.objects.filter(username__startswith='qa09close_').exists()
author=U.objects.create_user('qa09close_author',email='close-author09@example.invalid',first_name='Fictional QA Close')
voter=U.objects.create_user('qa09close_voter',email='close-voter09@example.invalid',first_name='Fictional QA Voter')
moderator=U.objects.get(username='qa09_admin')
place=create_ready_place(name='Fictional QA09 close place',name_az='Uydurma QA09 close',name_ru='Вымышленное QA09 close',name_en='Fictional QA09 close',owner=moderator,created_by=moderator,status='published',is_active=True)
specialist=Specialist.objects.create(name='Fictional QA09 close specialist',status='published',is_active=True)
cases={}
for kind,target in [('place',place),('specialist',specialist)]:
 h,old=submit_review(target=target,user=author,rating=4,text='QA09 CLOSE OLD '+kind,author_name='Fictional QA09 Close')
 moderate_candidate(head=h,revision_id=old.pk,actor=moderator,approve=True)
 h,new=submit_review(target=target,user=author,rating=5,text='QA09 CLOSE NEW '+kind,author_name='Fictional QA09 Close',expected_revision_id=old.pk)
 cases[kind]={'target_id':target.pk,'head_id':h.pk,'old_revision':old.pk,'new_revision':new.pk,'new_text':'QA09 CLOSE NEW '+kind}
(QA/'fixtures.json').write_text(json.dumps({'synthetic_only':True,'author_id':author.pk,'voter_id':voter.pk,'cases':cases},indent=2));print(json.dumps({'synthetic_users':2,'owned_targets':2,'heads':2,'initial_approved_and_pending_revisions':4}))
