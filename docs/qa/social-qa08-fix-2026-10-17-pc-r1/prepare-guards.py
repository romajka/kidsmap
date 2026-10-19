import json
from pathlib import Path
Q=Path(__file__).resolve().parent
(Q/'guard_fixtures.py').write_text('''import json
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from catalog.models import Organization,WorkflowNotification
from catalog.services import business_team
from catalog.testcases.utils import create_ready_place
@transaction.atomic
def seed():
 U=get_user_model();assert not U.objects.filter(username__startswith='s08-fix-guard-').exists();cases=json.loads((settings.QA_ROOT/'cases.json').read_text());guards=[]
 for kind in ['place','organization']:
  for lang in ['az','ru','en']:
   key='guard-'+kind+'-'+lang;owner=U.objects.create_user('s08-fix-guard-owner-'+key,email='owner-'+key+'@example.invalid');recipient=U.objects.create_user('s08-fix-guard-recipient-'+key,email='old-'+key+'@example.invalid')
   target=create_ready_place(owner=owner,created_by=owner,name='Fictional guard') if kind=='place' else Organization.objects.create(owner=owner,created_by=owner,name_az='Fictional guard')
   opts={'scope':'all_network'} if kind=='organization' else {}
   inv=business_team.invite(actor=owner,target_type=kind,target_id=target.pk,email=recipient.email,**opts);n=WorkflowNotification.objects.get(event_kind='team_invitation',entity_type=kind+'_team_invitation',entity_id=inv.pk)
   recipient.email='changed-'+key+'@example.invalid';recipient.save(update_fields=['email'])
   item=dict(key=key,kind=kind,lang=lang,width=390,owner=owner.username,recipient=recipient.username,email=recipient.email,target_id=target.pk,notice_id=n.pk,invitation_id=inv.pk);cases.append(item);guards.append(item)
 (settings.QA_ROOT/'cases.json').write_text(json.dumps(cases,indent=2));(settings.QA_ROOT/'guard-cases.json').write_text(json.dumps(guards,indent=2));print('Six own changed-email fixture cases created; original pending invites retained, no grant')
''')
p=Q/'runtime.py';t=p.read_text().replace("elif command == 'serve':", "elif command == 'guards_seed':\n    import guard_fixtures\n    guard_fixtures.seed()\nelif command == 'serve':");p.write_text(t)
(Q/'run_json.py').write_text((Q.parent/'social07-pc-fix-r1/run_json.py').read_text())
print('Separate own fixture command prepared, no server restart or application edits')
