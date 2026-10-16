import json
from pathlib import Path
from django.contrib.auth import get_user_model
from django.utils import timezone
from catalog.models import Organization,Program,Activity
from catalog.testcases.utils import create_ready_place
P=Path(__file__).resolve().parent;R=P.parents[2];sec=json.loads((R/'.tmp'/P.name/'credentials.json').read_text());U=get_user_model()
owner=U.objects.create_user('offerqa08fix_owner',email='offerqa08fix_owner@example.invalid',password=sec['owner_password']);admin=U.objects.create_superuser('offerqa08fix_admin',email='offerqa08fix_admin@example.invalid',password=sec['owner_password'])
org=Organization.objects.create(owner=owner,created_by=owner,name_az='Uydurma OFFER08 network',name_ru='Вымышленная сеть OFFER08',name_en='Fictional OFFER08 network',status='published',approved_at=timezone.now())
program=Program.objects.create(organization=org,created_by=owner,name_az='Uydurma OFFER08 program',description_az='APPROVED original OFFER08',status='published',approved_at=timezone.now())
place=create_ready_place(owner=owner,created_by=owner,name='Fictional OFFER08 branch',name_az='Uydurma OFFER08 branch')
from catalog.services import organization_ownership
organization_ownership.request_join(actor=owner,place_id=place.pk,organization_id=org.pk);place.refresh_from_db()
a=Activity.objects.create(place=place,program=program,name_az='Local OFFER08 activity',status='published',program_snapshot={'description_az':program.description_az})
(P/'fixtures.json').write_text(json.dumps({'owner_email':owner.email,'admin_username':admin.username,'organization':org.pk,'program':program.pk,'place':place.pk,'activity':a.pk},indent=2))
print('Fictional08 prerequisites created in own08 DB only; no candidate decision setup.')
