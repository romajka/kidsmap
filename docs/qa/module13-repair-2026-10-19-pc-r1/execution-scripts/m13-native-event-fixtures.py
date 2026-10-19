import sys,json
sys.argv=['runtime.py','event-fixtures'];from pathlib import Path
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/m13-full-r1');from runtime import *
from catalog.models import Event,Place,Organization
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
ids=json.loads((QA/'fixtures.json').read_text());old=Event.objects.get(pk=ids['event']);assert old.occurrence_state=='cancelled'
extra={}
for fmt in ['physical','online']:
 e=Event.objects.create(name='M13 Fresh '+fmt,name_az='M13 Fresh '+fmt,name_ru='M13 Fresh '+fmt,name_en='M13 Fresh '+fmt,owner=old.owner,status='published',category=old.category,event_format=fmt,organizer_organization=old.organizer_organization,related_place_id=ids['place'] if fmt=='physical' else None,start_datetime=timezone.now()+timedelta(days=8),end_datetime=timezone.now()+timedelta(days=8,hours=1),photo=old.photo,address='Fictional venue Module13' if fmt=='physical' else '')
 extra[fmt]=e.pk
ids['event']=extra['physical'];(QA/'fixtures.json').write_text(json.dumps(ids,indent=2));(QA/'event-fixtures.json').write_text(json.dumps(extra,indent=2));print('Two fresh identities for accepted native physical+online cases. Failed-attempt cancelled identity retained.')
