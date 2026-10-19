import sys,json
sys.argv=['runtime.py','readback'];from runtime import *
from django.db import transaction,connection
from catalog.models import WorkflowNotification,OwnerTeamInvitation,OwnerTeamMembership,OrganizationGrant,EmailOutbox
before=json.loads((QA/'fixture-info.json').read_text())
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
 counts=dict(notifications=WorkflowNotification.objects.count(),unread=WorkflowNotification.objects.filter(read_at__isnull=True).count(),outbox=EmailOutbox.objects.count(),memberships=OwnerTeamMembership.objects.count(),grants=OrganizationGrant.objects.count())
 status=OwnerTeamInvitation.objects.get(pk=before['revoked']['invitation_id']).status
output=dict(before=before['business_counts'],after=counts,business_counts_unchanged=counts==before['business_counts'],revoked_status=status,revoked_unchanged=status==before['revoked']['status'],authentication_writes='Expected fictional sessions/last_login only; not included in business mutation checks')
(QA/'readback.json').write_text(json.dumps(output,indent=2));assert output['business_counts_unchanged'] and output['revoked_unchanged'];print('Business aggregate and revoked-status readbacks PASS')
