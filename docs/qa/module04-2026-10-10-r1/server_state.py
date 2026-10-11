"""Read-only proof of fresh UI writes; never mutate Event."""
import sys,json
phase=sys.argv[1]
sys.argv=['run.py','qa-read']
from run import *
from django.db import connection,transaction
from django.utils import translation,timezone
from zoneinfo import ZoneInfo
from catalog.models import Event,EventOccurrenceChange
with transaction.atomic():
 with connection.cursor() as cur:cur.execute('SET TRANSACTION READ ONLY')
 rows=[]
 for e in Event.objects.order_by('pk'):
  with translation.override('ru'):url=e.get_absolute_url()
  rows.append({'id':e.pk,'status':e.status,'public':e.is_public,'url':url,'organizer_org':e.organizer_organization_id,'organizer_person':e.organizer_specialist_id,'format':e.event_format,'related_place':e.related_place_id,'name_az':e.name_az,'name_ru':e.name_ru,'name_en':e.name_en,'description_az':e.description_az,'description_ru':e.description_ru,'description_en':e.description_en,'address':e.address,'district':e.district,'lat':str(e.lat) if e.lat is not None else None,'lng':str(e.lng) if e.lng is not None else None,'phone':e.phone,'age_from':e.age_from,'age_to':e.age_to,'price':e.price_text,'photo':e.photo.name,'start_utc':str(e.start_datetime),'end_utc':str(e.end_datetime),'start_baku':str(timezone.localtime(e.start_datetime,ZoneInfo('Asia/Baku'))) if e.start_datetime else None,'end_baku':str(timezone.localtime(e.end_datetime,ZoneInfo('Asia/Baku'))) if e.end_datetime else None,'revision':e.updated_at.isoformat(),'reason':e.rejection_reason,'snapshot':e.venue_snapshot,'occurrence':e.occurrence_state,'gallery':list(e.gallery.order_by('order','id').values('id','image','order')),'changes':list(EventOccurrenceChange.objects.filter(event=e).values('id','kind','reason','version'))})
(HERE/f'server-{phase}.json').write_text(json.dumps(rows,ensure_ascii=False,default=str,indent=2),encoding='utf-8')
print('Read-only Event snapshot:',phase,'count',len(rows))
