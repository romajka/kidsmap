"""Setup for detach consequences/expiry only. No affiliation/ownership mutation."""
import sys,json
from datetime import timedelta
sys.argv=['run.py','observe']
from run import *
from django.utils import timezone
from django.contrib.auth import get_user_model
from catalog.models import Organization,Place,Program,Activity,OrganizationTeamInvitation
from catalog.services.organization_ownership import affiliation_current,approved_program_data
org=Organization.objects.get(pk=1);place=Place.objects.get(pk=11)
assert affiliation_current(place,org)
program=Program.objects.create(organization=org,created_by=org.owner,name_az='QA02 Shared approved program',description_az='QA02 synthetic common program',status='published',approved_at=timezone.now())
activity=Activity.objects.get(place=place)
activity.program=program;activity.program_snapshot=approved_program_data(program);activity.status='published';activity.save()
expired=OrganizationTeamInvitation.objects.create(organization=org,owner=org.owner,base_ownership_version=org.ownership_version,email='newowner@example.invalid',role='MODERATOR',actions=['place.view','place.stats.view'],scope='all_network',expires_at=timezone.now()-timedelta(days=1))
(HERE/'dependency-fixtures.json').write_text(json.dumps({'program':program.pk,'activity':activity.pk,'place':11,'expired_invitation':expired.pk,'expiry':'SIMULATED historical timestamp fixture; no external clock/GPS/mail'},indent=2),encoding='utf-8')
print('Shared program/linked activity setup and expired invitation fixture; affiliation remains canonical/UI-created')
