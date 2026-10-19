import sys,json
from datetime import timedelta
sys.argv=['runtime.py','seed-extra'];from runtime import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from catalog.models import Place,OwnerTeamMembership,AnalyticsActorExclusion,FunnelEvent
ids=json.loads((QA/'fixtures.json').read_text());place=Place.objects.get(pk=ids['place']);owner=get_user_model().objects.get(username='m12_owner')
for role in ['member','excluded','moderator','editor']:
 assert not get_user_model().objects.filter(username='m12_'+role).exists()
 user=get_user_model().objects.create_user('m12_'+role,email=role+'@example.invalid',password='fictional-only')
 if role=='excluded':AnalyticsActorExclusion.objects.create(user=user,reason_code='staff_test')
 if role in ['moderator','editor']:OwnerTeamMembership.objects.create(place=place,owner=owner,member=user,role=role.upper())
assert FunnelEvent.objects.count()==0
for days in [40,1]:
 for kind in ['place_view','phone_click']:FunnelEvent.objects.create(place=place,event_type=kind,schema_version=2,subject_type='place',subject_id=place.pk,occurred_at=timezone.now()-timedelta(days=days),visitor_key_hash='v1:fictional-initial-history',session_key_hash='v1:fictional-initial-history')
print('Own additional synthetic actors/team/exclusions and four explicit initial-history events seeded.')
