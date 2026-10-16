"""Explicit fictional fixture changes for negative ACL/venue checks; not a tested business transition."""
import json,sys
from pathlib import Path
from django.conf import settings
from django.db import connection,transaction
from catalog.models import Organization,Specialist,Place,Event
P=Path(__file__).resolve().parent;G=json.loads((P/'fixtures.json').read_text());E=json.loads((P.parent/'module04-recheck-2026-10-13-r1/entities.json').read_text());action=sys.argv[-1]
assert settings.TESTING and settings.QA_ROOT.name=='module04-recheck-2026-10-13-r1'
if action=='readback':
 with transaction.atomic():
  with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
  values=list(Event.objects.filter(pk__in=[E['venue'],E['person']]).values('pk','name_az','updated_at'))
 baseline=settings.QA_ROOT/'stimulus-before.json';old=json.loads(baseline.read_text()) if baseline.exists() else None
 result={'event_snapshot_unchanged':old==json.loads(json.dumps(values,default=str)),'read_only':True}
 (P/'stimulus-readback.json').write_text(json.dumps(result));print(json.dumps(result))
else:
 if action in ['revoke-org','hide-venue','reassign-person']:
  values=list(Event.objects.filter(pk__in=[E['venue'],E['person']]).values('pk','name_az','updated_at'));(settings.QA_ROOT/'stimulus-before.json').write_text(json.dumps(values,default=str))
 if action in ['revoke-org','restore-org']:
  obj=Organization.objects.get(pk=G['organization']);assert obj.name_az.startswith('Synthetic');obj.owner_id=G['actors']['outsider' if action=='revoke-org' else 'owner'];obj.save(update_fields=['owner'])
 elif action in ['hide-venue','restore-venue']:
  obj=Place.objects.get(pk=G['venues']['public']);assert obj.name_az.startswith('Synthetic');obj.is_active=action=='restore-venue';obj.save(update_fields=['is_active'])
 elif action in ['reassign-person','restore-person']:
  obj=Specialist.objects.get(pk=G['specialist']);assert obj.name.startswith('Synthetic');obj.verified_person_user_id=G['actors']['outsider' if action=='reassign-person' else 'person'];obj.save(update_fields=['verified_person_user'])
 else:raise ValueError('Unknown own fixture action')
 print(json.dumps({'action':action,'fictional_fixture_only':True,'event_orm_writes':0}))
