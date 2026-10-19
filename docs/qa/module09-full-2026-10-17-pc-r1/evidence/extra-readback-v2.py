import sys,json
sys.argv=['runtime.py','extra-readback'];from runtime import *
from django.db import transaction,connection
from catalog.models import OwnerTeamInvitation,OrganizationTeamInvitation,OwnerTeamMembership,OrganizationGrant,EmailOutbox,WorkflowNotification
cases=json.loads((QA/'extra-cases.json').read_text());rows=[]
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'")
 for item in cases['cases']:
  kind=item['kind'];model=OwnerTeamInvitation if kind=='place' else OrganizationTeamInvitation
  status=model.objects.get(pk=item['invitation_id']).status
  count=(OwnerTeamMembership.objects.filter(member_id=item['user_id'],place_id=item['target_id']) if kind=='place' else OrganizationGrant.objects.filter(member_id=item['user_id'],organization_id=item['target_id'])).count()
  decision=WorkflowNotification.objects.filter(event_kind='team_invitation_decision',entity_type=kind+'_team_invitation',entity_id=item['invitation_id'],entity_version=2)
  decisions=decision.count();mails=EmailOutbox.objects.filter(notification__in=decision).count()
  rows.append(dict(key=item['key'],status=status,grants=count,decision_count=decisions,decision_outbox_count=mails,passed=status=='ACCEPTED' and count==1 and decisions==1 and mails==1))
 count=EmailOutbox.objects.count()
output=dict(rows=rows,no_duplicate_outbox=count==cases['outbox_before']+len(cases['cases']),outbox_before=cases['outbox_before'],outbox_after=count)
(QA/'extra-readback-v2.json').write_text(json.dumps(output,indent=2));assert all(r['passed'] for r in rows) and output['no_duplicate_outbox'];print('Six invitation/grant/one-decision-each and exact+6outbox readbacks PASS')
