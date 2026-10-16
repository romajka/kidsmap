from datetime import timedelta
from django.utils import timezone
from catalog.models import Event,Specialist
import json
fixture=json.loads((HERE/'fixtures.json').read_text());now=timezone.now();records={}
for model in (Event,Specialist):
 rows=[]
 for i in range(107):
  n=(i*37)%107;title=f'SORTQA {n//2:03d}'
  values={'name':title,'status':'published' if i<105 else 'draft','photo':fixture['fixture_media']}
  if model is Event:values.update(category_id='EDU',start_datetime=now+timedelta(days=30),name_az=title,name_ru=title,name_en=title)
  else:values.update(consultation_format='online',is_active=True)
  o=model.objects.create(**values);created=(i*13)%23;updated=(i*7)%19
  model.objects.filter(pk=o.pk).update(created_at=now+timedelta(days=created),updated_at=now+timedelta(days=updated))
  if i<105:rows.append({'pk':o.pk,'name':title,'created':created,'updated':updated})
 records[model._meta.model_name]=rows
fixture['sorting_records']=records;fixture['queue_totals']={'event':110,'specialist':110};fixture['page_sizes']={'event':15,'specialist':100}
(HERE/'fixtures.json').write_text(json.dumps(fixture,indent=2));print('Own sorting fixtures:107 per queue,105 published matching rows')
