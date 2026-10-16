import io,json
from pathlib import Path
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from catalog.services.place_schedule import parse_schedule_payload,sync_place_schedule
from catalog.testcases.utils import create_ready_place,build_structured_schedule_payload
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());owner=get_user_model().objects.get(username=F['users']['owner']['username']);b=io.BytesIO();Image.new('RGB',(900,600),'#65a898').save(b,format='PNG');cells=[]
for lang in ['ru','az','en']:
 place=create_ready_place(owner=owner,created_by=owner,name='Fictional OFFER04 '+lang,name_az='Uydurma OFFER04 '+lang,name_ru='Вымышленное OFFER04 '+lang,name_en='Fictional OFFER04 '+lang,city='baku',district='baku_yasamal',schedule_mode='regular');place.photo.save('fictional-offer04.png',ContentFile(b.getvalue()),save=True)
 days=parse_schedule_payload(build_structured_schedule_payload());days[0]['intervals']=[{'start':'09:00','end':'12:00'},{'start':'14:00','end':'18:00'}];sync_place_schedule(place,days);cells.append({'lang':lang,'place':place.pk})
F['cells']=cells;(P/'fixtures.json').write_text(json.dumps(F,ensure_ascii=False,indent=2));print(json.dumps({'own_new_fictional_places':len(cells),'mode':'regular','monday_intervals':2}))
