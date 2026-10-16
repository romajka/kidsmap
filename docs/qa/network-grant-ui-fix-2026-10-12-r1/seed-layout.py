"""Fictional long-name/topology fixture only; no tested network grants/invitations."""
import json
from pathlib import Path
from django.contrib.auth import get_user_model
from catalog.models import Organization
from catalog.services import organization_ownership
from catalog.testcases.utils import create_quality_place
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
secret=json.loads((ROOT/'.tmp'/HERE.name/'credentials.json').read_text())
fixtures=json.loads((HERE/'fixtures.json').read_text())
member=get_user_model().objects.create_user(username='network_long_'+('member'*20),email='network-long@example.invalid',password=secret['owner_password'])
fixtures['actors']['longmember']={'id':member.pk,'username':member.username,'email':member.email}
(HERE/'fixtures.json').write_text(json.dumps(fixtures))
owner=get_user_model().objects.get(pk=fixtures['actors']['owner']['id'])
cases=json.loads((HERE/'case-fixtures.json').read_text())
for lang in ('ru','az','en'):
    org=Organization.objects.create(owner=owner,created_by=owner,name_az='NETWORK fictional '+lang+' layout')
    place=create_quality_place(owner=owner,created_by=owner,name_az='NETWORK fictional '+lang+' layout branch')
    organization_ownership.request_join(actor=owner,place_id=place.pk,organization_id=org.pk)
    cases[lang+'-layout']={'organization_id':org.pk,'place_id':place.pk}
(HERE/'case-fixtures.json').write_text(json.dumps(cases,indent=2))
print(json.dumps({'fictional_layout_orgs':3,'long_name_fixture':True,'tested_network_grants_created':0}))
