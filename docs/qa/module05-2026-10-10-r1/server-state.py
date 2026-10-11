"""Read-only synthetic state evidence, never save audited transitions."""
import sys,json
label=sys.argv[1];sys.argv=['run.py','qa-read']
from run import *
from django.db import connection,transaction
from catalog.models import Program,Activity,OfferingGroup,PricingPlan,Place,VolunteerPlaceRevision,PlaceScheduleDay,PlaceScheduleInterval,OrganizationGrant
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'")
 out={m.__name__:list(m.objects.values(*fields).order_by('pk')) for m,fields in [
 (Program,('id','organization_id','name_az','name_ru','status','content_version','archived_at')),
 (Activity,('id','place_id','program_id','name_az','status','content_version','archived_at','program_snapshot','source_program_id','source_program_version')),
 (OfferingGroup,('id','activity_id','name_az','age_from','age_to','schedule_text','conditions_az','conditions_verified_at','content_version','archived_at')),
 (PricingPlan,('id','place_id','offering_group_id','product_type','title_az','price_kind','price','price_min','price_max','currency','quantity','quantity_unit','billing_mode','billing_interval','billing_interval_count','age_from','age_to','is_active')),
 (Place,('id','name_az','organization_id','content_version','status','price_mode','price_from','price_to','schedule_mode','schedule')),
 (VolunteerPlaceRevision,('id','place_id','program_id','activity_id','offering_group_id','status','version','payload','changed_fields','review_note')),
 (PlaceScheduleDay,('id','place_id','weekday','is_closed')),
 (PlaceScheduleInterval,('id','schedule_day_id','start_time','end_time')),
 (OrganizationGrant,('id','organization_id','member_id','scope','is_active','version'))]}
(HERE/('state-'+label+'.json')).write_text(json.dumps(out,indent=2,default=str),encoding='utf-8');print('Read-only state',label,{k:len(v) for k,v in out.items()})
