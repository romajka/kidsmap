import json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m12-full-r1';O=R/'docs/qa/module12-repair-2026-10-18-pc-r1'
t=(Q/'qa_urls.py').read_text();t=t.replace("['admin','owner','viewer','denied']","['admin','owner','viewer','denied','member','excluded','moderator','editor']")
old="'simulation':__import__('qa_simulation').COUNTERS}"
new="'simulation':__import__('qa_simulation').COUNTERS,'metrics':__import__('dataclasses').asdict(__import__('catalog.services.analytics_metrics',fromlist=['build_subject_metrics']).build_subject_metrics(subject_type='place',subject_ids=[ids['place']],start=__import__('django.utils.timezone',fromlist=['now']).now()-__import__('datetime').timedelta(days=30),end=__import__('django.utils.timezone',fromlist=['now']).now())),'place_state':{'names':{lang:getattr(objects['place'],'name_'+lang) for lang in ['az','ru','en']},'is_active':objects['place'].is_active,'status':objects['place'].status,'website':objects['place'].website,'instagram':objects['place'].instagram}}"
assert old in t;t=t.replace(old,new);(Q/'qa_urls.py').write_text(t)
t=(Q/'qa_simulation.py').read_text().replace('from unittest.mock import patch','from unittest.mock import patch\nfrom django.test import override_settings');t=t.replace("        mode=json.loads", "        if request.path.startswith(('/static/','/media/','/qa/')):\n            return self.get_response(request)\n        mode=json.loads");t=t.replace('        with ExitStack() as stack:','        with ExitStack() as stack:\n            if mode[\'storage\']==\'disabled\':stack.enter_context(override_settings(LOCAL_ANALYTICS_STORAGE_ENABLED=False))');(Q/'qa_simulation.py').write_text(t)
code="""import sys,json
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
"""
(Q/'seed-extra.py').write_text(code);p=subprocess.run(['docker','exec','m12full-r1-app','python',str(Q/'seed-extra.py')],capture_output=True,text=True);(Q/'seed-extra.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-500:]
(Q/'simulation.json').write_text(json.dumps({'report':'disabled','storage':'healthy'}));(O/'evidence/native-current-source.json').write_bytes((Q/'expected-source.json').read_bytes());(O/'evidence/extra-fixture-note.md').write_text('Own fixture initialization only:4additional fictional actors,2scoped team roles,1active synthetic exclusion and4explicit initial-history events at days40/1. No old/production history backfill. Previous report matrices completed before this initialization and proved their own events/media/entity unchanged. Subsequent native deltas start from this new documented baseline. No raw hashes/sessions/user records exported. Faults and disabled-collection override in QA middleware explicitly SIMULATED.')
