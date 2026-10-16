import json
from pathlib import Path
from django.contrib.auth import get_user_model
from catalog.models import Organization,Place,Category
from catalog.services.organization_ownership import create_organization
P=Path(__file__).resolve().parent
u=get_user_model().objects.get(username='start_admin');cat=Category.objects.get(code='EDU')
org=create_organization(actor=u,values={'name_az':'QA02 LOCAL təşkilat','name_ru':'QA02 LOCAL сеть','name_en':'QA02 LOCAL network'})
places=[Place.objects.create(name='QA02 LOCAL BULK '+str(i),name_az='QA02 LOCAL BULK '+str(i),name_ru='QA02 LOCAL BULK '+str(i),name_en='QA02 LOCAL BULK '+str(i),owner=u,created_by=u,category=cat,status='draft',is_active=False).pk for i in range(3)]
(P/'fixtures.json').write_text(json.dumps({'organization_id':org.pk,'place_ids':places,'admin':'start_admin'}))
print('Own fictional seed ready')
