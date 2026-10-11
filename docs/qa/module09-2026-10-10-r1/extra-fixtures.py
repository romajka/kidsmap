"""New initial positive-ACL cases; not transitions on already audited objects."""
import sys,json
sys.argv=['run.py','qa-extra'];from run import *
from catalog.models import *
from catalog.testcases.utils import create_ready_place
from catalog.services.review_versions import submit_review,moderate_candidate
from django.contrib.auth import get_user_model
from django.utils import timezone
U=get_user_model();f=json.loads((HERE/'fixtures.json').read_text());a={r:U.objects.get(pk=v['id']) for r,v in f['actors'].items()}
assert not Place.objects.filter(name='Fictional QA09 granted').exists()
p=create_ready_place(name='Fictional QA09 granted',name_az='Uydurma QA09 granted',owner=a['owner'],created_by=a['owner'],photo='places/qa09.png')
grant=OwnerTeamMembership.objects.create(place=p,owner=a['owner'],member=a['employee'],role='EDITOR',actions=['place.reviews.reply','place.reviews.report'],base_ownership_version=p.ownership_version)
spec=Specialist.objects.create(name='Fictional QA09 verified person',name_alt='Uydurma QA09 təsdiqlənmiş şəxs',owner=a['owner'],verified_person_user=a['owner'],person_verified_at=timezone.now(),status='published',is_active=True)
data={'place':p.pk,'specialist':spec.pk,'reviews':{}}
for kind,target in [('place',p),('specialist',spec)]:
 h,v=submit_review(target=target,user=a['author'],rating=5,text='QA09 INITIAL ACL '+kind,author_name='Fictional author');moderate_candidate(head=h,revision_id=v.pk,actor=a['admin'],approve=True);data['reviews'][kind]=h.pk
(HERE/'extra-fixtures.json').write_text(json.dumps(data,indent=2));print('New positive-ACL initial cases only')
