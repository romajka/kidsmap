"""Make the fictional employee grant genuine before its final ACL control."""
from django.contrib.auth import get_user_model
from catalog.models import Organization,OrganizationGrant
from catalog.services.business_team import has_action
u=get_user_model().objects.get(username='specqa_employee');org=Organization.objects.get(pk=1);g=OrganizationGrant.objects.get(organization=org,member=u)
g.actions=['organization.view','organization.edit','place.view','place.edit'];g.save(update_fields=['actions'])
assert has_action(user=u,target=org,action='organization.view')
assert has_action(user=u,target=org,action='organization.edit')
print('Fictional current employee has genuine organization view/edit actions; private-person tests remain UI-only.')
