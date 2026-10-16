"""READ ONLY aggregate audit of this run's fictional state and filebased emails."""
import contextlib,io,json,re,runpy,socket,sys
from collections import Counter
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
sys.argv=[str(H/'runtime.py'),'readback']
with contextlib.redirect_stdout(io.StringIO()):runpy.run_path(str(H/'runtime.py'),run_name='owned_audit_bootstrap')
from django.db import connection,transaction
from django.utils import timezone
from catalog.models import (OwnerTeamInvitation,OrganizationTeamInvitation,OwnerTeamMembership,
                            OrganizationGrant,WorkflowNotification,EmailOutbox)
f=json.loads((S/'fixtures.json').read_text());states=[]
with transaction.atomic():
 with connection.cursor()as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'");c.execute('SELECT count(*) FROM django_migrations');migrations=c.fetchone()[0]
 for key,user in f['users'].items():
  if key in ('owner','recipient','other'):continue
  expected='ACCEPTED'if key.startswith('accept_')else'REJECTED'if key.startswith(('tabs_','network_'))or key=='nojs'else'PENDING'if key.startswith(('email_','expiry_'))else'CANCELED'
  for kind,model,grants in [('place',OwnerTeamInvitation,OwnerTeamMembership),('organization',OrganizationTeamInvitation,OrganizationGrant)]:
   row=model.objects.filter(email=user['email']).order_by('-pk').first();assert row is not None,key
   count=WorkflowNotification.objects.filter(event_kind='team_invitation_decision',entity_type=f'{kind}_team_invitation',entity_id=row.pk).count()
   grant_count=grants.objects.filter(member_id=user['id'],is_active=True).count()
   ok=row.status==expected and grant_count==(1 if expected=='ACCEPTED'else 0)and count==(1 if expected in ('ACCEPTED','REJECTED')else 0)
   if key.startswith('expiry_'):ok=ok and row.expires_at<=timezone.now()
   assert ok,(key,kind,row.status,expected,count,grant_count)
   states.append({'scenario':key.split('_',1)[0],'type':kind,'status':row.status,'correct_grant_count':True,'correct_decision_count':True})
 aggregate={'place_statuses':dict(Counter(OwnerTeamInvitation.objects.values_list('status',flat=True))),'organization_statuses':dict(Counter(OrganizationTeamInvitation.objects.values_list('status',flat=True))),'place_grants':OwnerTeamMembership.objects.count(),'organization_grants':OrganizationGrant.objects.count(),'notification_count':WorkflowNotification.objects.count(),'outbox_statuses':dict(Counter(EmailOutbox.objects.values_list('status',flat=True))),'migrations':migrations}
 assert aggregate['place_grants']==aggregate['organization_grants']==6
 # Every historical accepted/rejected invitation has exactly one decision; all others have none.
 for kind,model in [('place',OwnerTeamInvitation),('organization',OrganizationTeamInvitation)]:
  for row in model.objects.all():
   count=WorkflowNotification.objects.filter(event_kind='team_invitation_decision',entity_type=f'{kind}_team_invitation',entity_id=row.pk).count()
   assert count==(1 if row.status in ('ACCEPTED','REJECTED')else 0),(kind,row.pk,row.status,count)
files=list((S/'email').glob('*.log'));messages=0;all_recipients_fictional=True
for p in files:
 data=p.read_text();messages+=len(re.findall(r'^MIME-Version:',data,re.M))
 for address in re.findall(r'^To: (.+)$',data,re.M):all_recipients_fictional &= address.strip().endswith('@example.invalid')
assert messages==aggregate['outbox_statuses'].get('sent',0)and all_recipients_fictional
assert not aggregate['outbox_statuses'].get('failed',0)and not aggregate['outbox_statuses'].get('retry',0)
denied=False
try:socket.create_connection(('203.0.113.1',443),timeout=1)
except RuntimeError:denied=True
assert denied
result={'read_only':True,'timeouts':'statement10s/lock2s','aggregate':aggregate,'checked_latest_invitation_scenarios':len(states),'scenario_results':states,'all_historical_terminal_decisions_unique':True,'local_email_files':len(files),'local_email_message_count':messages,'all_recipients_fictional':bool(all_recipients_fictional),'external_connect_denied':denied,'email_scheduler':'SIMULATED manual tick; real own filebased messages, not SMTP'}
(H/'readback-final.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='scenario_results'}))
