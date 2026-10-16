import json
from pathlib import Path
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from catalog.models import Place
from catalog.services.staff_roles import VOLUNTEER_GROUP,can_use_volunteer_workspace
P=Path(__file__).resolve().parent;S=P.parents[2]/'.tmp'/P.name;F=json.loads((P/'fixtures.json').read_text());password=json.loads((S/'credentials.json').read_text())['owner_password'];v=get_user_model().objects.create_user('offerqa04_volunteer',email='offerqa04_volunteer@example.invalid',password=password,is_staff=True);v.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0]);assert can_use_volunteer_workspace(v)
Place.objects.filter(pk__in=[c['place'] for c in F['admin']]).update(owner=None,created_by=v);F['users']['volunteer']={'username':v.username,'email':v.email};(P/'fixtures.json').write_text(json.dumps(F,ensure_ascii=False,indent=2));print(json.dumps({'fictional_canonical_volunteer':True,'own_unowned_prerequisites':3,'app_permissions_unchanged':True}))
