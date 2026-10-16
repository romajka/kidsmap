"""Repair only the fictional stand's submitted revision metadata."""
import json
from pathlib import Path
from catalog.models import PlaceOwnershipRequest, VolunteerPlaceRevision
from catalog.services import publication

HERE = Path(__file__).resolve().parent
fixtures = json.loads((HERE / 'fixtures.json').read_text())
item = PlaceOwnershipRequest.objects.select_related('place', 'applicant').get(pk=fixtures['request'])
assert item.applicant.username == 'preview_owner' and item.status == 'PENDING'
revision = VolunteerPlaceRevision.objects.get(pk=fixtures['revision'], place=item.place)
assert revision.status == 'pending' and set(revision.payload) == {'description_ru'}
revision.dependencies = publication.dependencies(item.place, 'place')
revision.changed_fields = ['description_ru']
revision.schema_version = publication.SCHEMA_VERSION
revision.save(update_fields=['dependencies', 'changed_fields', 'schema_version'])
print('Fictional submitted revision uses current review metadata.')
