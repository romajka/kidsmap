import sys,json
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/m13-full-r1');sys.argv=['runtime.py','people-fixtures'];from runtime import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from catalog.models import Specialist,SpecialistPracticeLocation,Place
from catalog.services import business_team
owner=get_user_model().objects.get(username='m13_owner');person=get_user_model().objects.get(username='m13_member');assert not Specialist.objects.filter(verified_person_user=person).exists()
s=Specialist.objects.create(name='M13 Confirmed Independent Person',owner=person,created_by=person,verified_person_user=person,person_verified_at=timezone.now(),status='published',is_active=True,consultation_format='both',photo=Specialist.objects.get(pk=1).photo,**{'bio_'+l:'M13 fictional person '+('Education and children practice. '*10) for l in ['az','ru','en']})
for place_id in [1,2]:SpecialistPracticeLocation.objects.create(specialist=s,place_id=place_id,is_active=True,is_primary=place_id==2,schedule='Monday 16:00',price_per_session=30)
invite=business_team.invite(actor=owner,target_type='organization',target_id=2,email=person.email,role='EDITOR',scope='all_network')
grant=business_team.accept(actor=person,target_type='organization',invitation_id=invite.pk)
(QA/'people-fixtures.json').write_text(json.dumps({'specialist':s.pk,'grant':grant.pk,'initial_fixture_only':True}));print('Initial confirmed person/practice and active network grant fixtures ready; native cooperation/revoke actions not performed by this script.')
