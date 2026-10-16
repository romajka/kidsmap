"""Fictional prerequisites; checked interval/copy/save transitions use native UI."""
import io,json
from pathlib import Path
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from catalog.testcases.utils import create_ready_place,build_structured_schedule_payload
from catalog.services.place_schedule import parse_schedule_payload,sync_place_schedule
P=Path(__file__).resolve().parent;S=P.parents[2]/'.tmp'/P.name;password=json.loads((S/'credentials.json').read_text())['owner_password'];actors={}
for role in ['owner','admin','outsider']:
 actors[role]=get_user_model().objects.create_user('offerqa04_'+role,email='offerqa04_'+role+'@example.invalid',password=password,is_staff=role=='admin',is_superuser=role=='admin')
b=io.BytesIO();Image.new('RGB',(900,600),'#65a898').save(b,format='PNG');sets={}
for kind in ['geometry','functional','admin']:
 cells=[]
 for lang in ['ru','az','en']:
  key=kind+'-'+lang;place=create_ready_place(owner=actors['owner'],created_by=actors['owner'],name='Fictional OFFER04 '+key,name_az='Uydurma OFFER04 '+key,name_ru='Вымышленное OFFER04 '+key,name_en='Fictional OFFER04 '+key,city='baku',district='baku_yasamal',schedule_mode='regular');place.photo.save('fictional-offer04-'+key+'.png',ContentFile(b.getvalue()),save=True)
  days=parse_schedule_payload(build_structured_schedule_payload());days[0]['intervals']=[{'start':'09:00','end':'12:00'},{'start':'14:00','end':'18:00'}];sync_place_schedule(place,days);cells.append({'lang':lang,'place':place.pk})
 sets[kind]=cells
sets['users']={k:{'username':u.username,'email':u.email} for k,u in actors.items()};sets['cells']=sets['geometry'];(P/'fixtures.json').write_text(json.dumps(sets,ensure_ascii=False,indent=2));print(json.dumps({'own_fictional_places':9,'roles':3,'regular_mon_intervals':2}))
