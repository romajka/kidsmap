"""Own synthetic staff business grants, distinct from platform review permissions."""
import sys
sys.argv=['run.py','qa-bootstrap']
from run import *
from catalog.models import Organization,OrganizationGrant,OwnerTeamMembership
o=Organization.objects.get(pk=1)
OrganizationGrant.objects.create(organization=o,owner_id=1,member_id=4,base_ownership_version=o.ownership_version,actions=['organization.view','program.manage','place.view','place.edit'],scope='all_network',role='EDITOR')
OwnerTeamMembership.objects.create(place_id=5,owner_id=1,member_id=4,role='EDITOR',base_ownership_version=1,is_active=True)
print('Synthetic staff granted explicit business editing; review permission alone does not grant it.')
