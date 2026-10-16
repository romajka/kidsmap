import json
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from catalog.models import Organization,Event
f=json.loads((HERE/'fixtures.json').read_text());owner=get_user_model().objects.get(pk=f['actors']['owner']['id']);assert cfg['database']=='module08_full_r1'
assert not(HERE/'extra-fixtures.json').exists()
org=Organization.objects.create(owner=owner,created_by=owner,name_az='Uydurma QA08 valid organizer',name_ru='Вымышленный QA08 организатор',name_en='Fictional QA08 organizer',status='published',description_az='Fictional own organizer')
event=Event.objects.create(owner=owner,name='Fictional QA08 valid event',name_az='Uydurma QA08 valid event',name_ru='Вымышленное QA08 мероприятие',name_en='Fictional QA08 valid event',category_id='EDU',organizer_organization=org,organizer_resolution='resolved',status='pending',event_format='online',start_datetime=timezone.now()+timedelta(days=4),end_datetime=timezone.now()+timedelta(days=4,hours=2),photo='places/qa08-live.png',phone='+994500000001',age_from=1,age_to=12,description_az='Uydurma tədbir. '*30,description_ru='Вымышленное мероприятие. '*30,description_en='Fictional event. '*30)
event.full_clean();f['valid_event']=event.pk;(HERE/'fixtures.json').write_text(json.dumps(f,indent=2));(HERE/'extra-fixtures.json').write_text(json.dumps({'new_initial_only':True,'event':event.pk,'organization':org.pk,'reason':'Initial event1 organizer owner=NULL, does not meet owner organizer contract. Existing fixture untouched; valid own organizer event2 prepared for positive native approval.'},indent=2));print(json.dumps({'new_event':event.pk,'new_organizer':org.pk}))
