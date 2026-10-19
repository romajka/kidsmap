import sys,json
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/m13-full-r1');sys.argv=['runtime.py','access-fixture'];from runtime import *
from django.contrib.auth import get_user_model
from catalog.models import OrganizationGrant,OwnerTeamMembership
from catalog.services import business_team
owner=get_user_model().objects.get(username='m13_owner');editor=get_user_model().objects.get(username='m13_editor')
assert OwnerTeamMembership.objects.filter(place_id=1,member=editor,is_active=True).exists()
assert not OrganizationGrant.objects.filter(organization_id=2,member=editor).exists()
invite=business_team.invite(actor=owner,target_type='organization',target_id=2,email=editor.email,role='EDITOR',scope='all_network');grant=business_team.accept(actor=editor,target_type='organization',invitation_id=invite.pk)
(QA/'editor-network-fixture.json').write_text(json.dumps({'grant':grant.pk,'initial_direct_place1_exists':True,'new_network_fixture_only':True}));print('Fresh editor network grant, with pre-existing actual direct Place1 membership, for complete native revoke replay. Member grant remains suspended.')
