import json,runpy,socket,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
sys.argv=[str(H/'runtime.py'),'readback'];runpy.run_path(str(H/'runtime.py'),run_name='qa_readback_runtime')
from django.db import transaction,connection
from catalog.models import WorkflowNotification,OwnerTeamInvitation,OrganizationTeamInvitation
with transaction.atomic():
 with connection.cursor()as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 f=json.loads((S/'fixtures.json').read_text());rows=list(WorkflowNotification.objects.filter(event_kind='team_invitation',recipient_user_id=f['users']['recipient']['id']))
 f['notifications']=[{'id':n.pk,'invitation_id':n.entity_id,'target_type':{'place_team_invitation':'place','organization_team_invitation':'organization'}[n.entity_type]}for n in rows]
 assert len(rows)==2
 assert list(OwnerTeamInvitation.objects.values_list('status',flat=True))==['PENDING']and list(OrganizationTeamInvitation.objects.values_list('status',flat=True))==['PENDING']
(S/'fixtures.json').write_text(json.dumps(f))
try:socket.create_connection(('203.0.113.1',443),timeout=1)
except RuntimeError:print(json.dumps({'external_connect_denied':True,'live_invitation_scope_map_saved_in_ignored_fixture':True}))
else:raise AssertionError('External connect allowed')
