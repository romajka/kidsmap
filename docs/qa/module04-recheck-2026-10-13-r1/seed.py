import json,io
from pathlib import Path
from datetime import timedelta
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from catalog.models import SiteSettings,Category,Organization,Event
P=Path(__file__).resolve().parent;S=P.parents[2]/'.tmp'/P.name
password=json.loads((S/'credentials.json').read_text())['owner_password']
roles={}
for role in ['owner','admin','outsider']:
 u=get_user_model().objects.create_user('eventqa_'+role,email=role+'@example.invalid',password=password,is_staff=role=='admin',is_superuser=role=='admin');roles[role]=u
flag=SiteSettings.get_solo();flag.events_section_enabled=True;flag.organizations_section_enabled=True;flag.save()
cat,_=Category.objects.get_or_create(code='EDU',defaults={'name_az':'Uydurma tədbir','name_ru':'Тестовое мероприятие','name_en':'Fictional event'})
org=Organization.objects.create(name_az='Synthetic module04 organizer',owner=roles['owner'],status='published',approved_at=timezone.now())
b=io.BytesIO();Image.new('RGB',(1200,1200),'#53a97c').save(b,format='PNG');(S/'assets').mkdir();(S/'assets/photo.png').write_bytes(b.getvalue())
values={'owner':roles['owner'],'organizer_organization':org,'category':cat,'name':'Synthetic module04 event','name_az':'Uydurma module04 tədbir','description_az':'Uydurma tədbirin təsviri. '*20,'event_format':'online','start_datetime':timezone.now()+timedelta(days=20),'end_datetime':timezone.now()+timedelta(days=20,hours=1),'phone':'+994500000041','photo':SimpleUploadedFile('event.png',b.getvalue()),'status':'draft'}
event=Event.objects.create(**values)
(P/'fixtures.json').write_text(json.dumps({'event':event.pk,'org':org.pk,'category':cat.code,'users':{k:v.username for k,v in roles.items()}}))
print(json.dumps({'synthetic_roles':len(roles),'draft_event':event.pk}))
