"""Publish only the fictional nested activity, while its Place stays pending."""
import json
from pathlib import Path
from catalog.models import PlaceOwnershipRequest, Activity
HERE=Path(__file__).resolve().parent
fixtures=json.loads((HERE.parent/'ownership-preview-fix-2026-10-14/fixtures.json').read_text())
item=PlaceOwnershipRequest.objects.select_related('applicant','place').get(pk=fixtures['request'])
assert item.applicant.username=='preview_owner' and item.status=='PENDING' and not item.place.is_public
Activity.objects.filter(place=item.place).update(status='published')
print('Fictional nested activity is published; fictional parent stays pending.')
