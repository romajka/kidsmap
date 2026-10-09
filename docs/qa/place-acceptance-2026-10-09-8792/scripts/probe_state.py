from django.db import transaction,connection
from catalog.models import Place,VolunteerPlaceRevision
import json
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute('SET LOCAL statement_timeout=20000');c.execute('SET LOCAL lock_timeout=2000')
 rows=[]
 for p in Place.objects.filter(pk__gte=158).order_by('pk'):
  r=VolunteerPlaceRevision.objects.filter(place=p).first()
  rows.append({'id':p.pk,'status':p.status,'public':p.is_public,'live':{k:getattr(p,k,None) for k in ('name_az','name_ru','name_en','description_az','description_ru','description_en','address','lat','lng','schedule_mode','price_mode','price_from','price_to','category_id','subcategory_id')},'organization_id':p.organization_id,'photo':bool(p.photo),'gallery':list(p.gallery.values('order','image')),'place_hours':[{'weekday':d.weekday,'closed':d.is_closed,'intervals':list(d.intervals.values('start_time','end_time'))}for d in p.schedule_days.all()],'tariffs':list(p.pricing_plan_records.values('title_az','product_type','price_kind','price')), 'revision':{'status':r.status,'review_note':r.review_note,'version':r.version,'base_content_version':r.base_content_version,'base_snapshot':r.base_snapshot,'payload':r.payload} if r else None})
 print(json.dumps({'rows':rows},default=str,ensure_ascii=False))
