"""Own fictional identity/venue fixtures; tested Event transitions remain native UI."""
import json
from pathlib import Path
from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from catalog.models import Organization,Specialist,Place,Category,SiteSettings
P=Path(__file__).resolve().parent;R=P.parents[2];S=R/'.tmp/module04-recheck-2026-10-13-r1'
password=json.loads((S/'credentials.json').read_text())['owner_password'];actors={}
for role in ['owner','person','outsider','empty','moderator','admin']:
 u,_=get_user_model().objects.get_or_create(username='eventqa_'+role,defaults={'email':role+'@example.invalid','is_staff':role in ['moderator','admin'],'is_superuser':role=='admin'})
 u.set_password(password);u.save();actors[role]=u
actors['moderator'].user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog',codename__in=['view_event','change_event','add_event']))
org=Organization.objects.get(owner=actors['owner']);foreign,_=Organization.objects.get_or_create(owner=actors['outsider'],name_az='Synthetic foreign organizer')
person,_=Specialist.objects.get_or_create(name='Synthetic event person',defaults={'verified_person_user':actors['person'],'person_verified_at':timezone.now(),'status':'published','is_active':True})
category=Category.objects.get(code='EDU');venues={}
for key,owner,status,active in [('own',actors['owner'],'draft',True),('public',actors['outsider'],'published',True),('foreign_draft',actors['outsider'],'draft',True),('hidden',actors['outsider'],'published',False)]:
 place,_=Place.objects.get_or_create(name_az='Synthetic venue '+key,defaults={'name':'Synthetic venue '+key,'description_az':'Uşaqlar üçün uydurma tədbir zalı. '*20,'category':category,'owner':owner,'created_by':owner,'status':status,'is_active':active,'city':'baku','district':'baku_yasamal','address':'Uydurma küçə 15 '+key,'phone1':'+994500000041','schedule_mode':'always_open','price_mode':'free','age_from':3,'age_to':12});venues[key]=place.pk
site=SiteSettings.get_solo();site.events_section_enabled=True;site.organizations_section_enabled=True;site.specialists_section_enabled=True;site.save()
for name,color in [('replacement','#abc4e5'),('gallery1','#d4a591'),('gallery2','#caba91')]:Image.new('RGB',(1200,1200),color).save(S/f'assets/{name}.png')
(S/'assets/corrupt.png').write_bytes(b'not a PNG');(S/'assets/invalid.txt').write_text('SYNTHETIC INVALID FILE')
fixture={'actors':{r:u.pk for r,u in actors.items()},'organization':org.pk,'foreign_organization':foreign.pk,'specialist':person.pk,'venues':venues,'category':'EDU','synthetic':True}
(P/'fixtures.json').write_text(json.dumps(fixture,indent=2));print(json.dumps({'fictional_roles':len(actors),'fictional_venues':len(venues),'event_orm_writes':0}))
