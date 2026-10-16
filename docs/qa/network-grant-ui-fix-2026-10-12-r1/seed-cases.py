"""Fictional topology/direct-permission fixtures; tested network transitions remain native UI."""
import json
from pathlib import Path
from django.contrib.auth import get_user_model
from catalog.models import Organization, OwnerTeamMembership, ServerDraft
from catalog.services import organization_ownership
from catalog.testcases.utils import create_quality_place, ensure_quality_subcategory
HERE=Path(__file__).resolve().parent
fixtures=json.loads((HERE/'fixtures.json').read_text())
owner=get_user_model().objects.get(pk=fixtures['actors']['owner']['id'])
member=get_user_model().objects.get(pk=fixtures['actors']['member']['id'])
ensure_quality_subcategory('EDU')
cases={}
for lang in ('ru','az','en'):
    for width in (390,1440):
        cell=f'{lang}-{width}'
        org=Organization.objects.create(owner=owner,created_by=owner,
                                       name_az='NETWORK fictional '+cell, name_en='Fictional live '+cell)
        places=[]
        for kind in ('direct','selected','unselected'):
            place=create_quality_place(owner=owner,created_by=owner,name_az='NETWORK fictional '+cell+' '+kind)
            organization_ownership.request_join(actor=owner,place_id=place.pk,organization_id=org.pk)
            places.append(place.pk)
        direct=OwnerTeamMembership.objects.create(place_id=places[0],owner=owner,member=member,role='EDITOR')
        cases[cell]={'organization_id':org.pk,'places':places,'direct_grant_id':direct.pk,
                     'scope':'selected_places' if width==390 else 'all_network'}
(HERE/'case-fixtures.json').write_text(json.dumps(cases,indent=2))
print(json.dumps({'fictional_organizations':6,'fictional_places':18,'direct_fixtures':6,
                  'tested_network_grants_created':0,'tested_invitations_created':0}))
