import json
from pathlib import Path
from datetime import timedelta
from django.utils import timezone
from catalog.models import OrganizationConnectionOperation
s=Path(__file__).parent;pk=json.loads((s/'browser_expiry_start.json').read_text())['operation']
op=OrganizationConnectionOperation.objects.get(pk=pk,actor__username='demo_owner',organization_id=43,action='detach',status='preview')
assert list(op.items.values_list('place_id',flat=True))==[81]
OrganizationConnectionOperation.objects.filter(pk=pk).update(expires_at=timezone.now()-timedelta(seconds=1))
print('Only own synthetic receipt expired')
