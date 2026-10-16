import json
from pathlib import Path
from django.db import connection,transaction
from django.contrib.auth import get_user_model
from catalog.models import Place,Program,Activity,OfferingGroup,PricingPlan,VolunteerPlaceRevision
from catalog.services.place_access import has_place_permission
from catalog.services.place_schedule import serialize_place_schedule
P=Path(__file__).resolve().parent;f=json.loads((P/'fixtures.json').read_text());checks=[]
def check(name,truth):
 checks.append({'id':name,'status':'PASS' if truth else 'FAIL'});assert truth,name
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 local=Place.objects.get(pk=f['venues']['local']);branch=Place.objects.get(pk=f['venues']['branch']);legacy=Place.objects.get(pk=f['venues']['legacy']);program=Program.objects.get(pk=f['program']);a=Activity.objects.get(pk=f['local_activity']);b=Activity.objects.get(pk=f['branch_activity']);g=OfferingGroup.objects.get(pk=f['local_groups'][0]);removed=OfferingGroup.objects.get(pk=f['local_groups'][1]);archived=Activity.objects.get(pk=f['archived_activity']);ag=OfferingGroup.objects.get(pk=f['archived_group']);ap=PricingPlan.objects.get(pk=f['archived_plan']);employee=get_user_model().objects.get(pk=f['actors']['employee'])
 check('approved-local-active-group20',local.activities.filter(archived_at__isnull=True).count()==1 and a.offering_groups.filter(archived_at__isnull=True).count()==1 and g.pricing_plan_records.filter(price=20,is_active=True).exists())
 check('removed-group-history80-preserved',removed.archived_at is not None and removed.pricing_plan_records.filter(price=80).exists())
 check('activity-archive-history15-preserved',archived.archived_at is not None and ag.archived_at is not None and ap.price==15 and ap.offering_group_id==ag.pk)
 check('conditions-reset-after-approved-change',g.conditions_verified_at is None and g.conditions_az=='Uydurma updated confirmed conditions module05')
 check('native-final-program-published',program.status=='published' and program.description_az=='FINAL republished common module05' and program.name_ru=='Fictional canonical B en 1440')
 check('detached-branch-keeps-local-price30',b.program_id is None and b.offering_groups.get(pk=f['branch_group']).pricing_plan_records.filter(price=30).exists())
 check('detached-branch-frozen-common-snapshot',b.program_snapshot.get('description_az')=='FINAL approved common module05')
 check('detached-organization-pointer-cleared',branch.organization_id is None)
 check('employee-detached-grant-no-edit',not has_place_permission(user=employee,place=branch,permission_code='place.edit'))
 check('legacy-scalars-and-text-preserved',legacy.price_from==31 and legacy.price_to==35 and legacy.schedule=='Bazar ertəsi 10:00–16:00')
 hours=serialize_place_schedule(local);check('saved-place-hours-two-intervals',len(hours[0]['intervals'])==2 and any(d['is_closed'] for d in hours))
 check('lesson-schedule-independent',g.schedule_text=='Bazar ertəsi 16:00–17:00')
 restored=Place.objects.get(pk=f['venues']['restore']);check('private-restore-keeps-approved-live',restored.activities.filter(name_az='NEW approved working module05',archived_at__isnull=True).exists())
 check('local-no-pending-invalid-candidate',not VolunteerPlaceRevision.objects.filter(place=local,status='pending').exists())
 d={'transaction':'READ ONLY','statement_timeout':'10s','lock_timeout':'2s','checks':checks,'local_group_plan_ids':list(g.pricing_plan_records.values_list('pk',flat=True)),'removed_group_plan_ids':list(removed.pricing_plan_records.values_list('pk',flat=True)),'program_status':program.status,'local_live_version':local.content_version,'detached_source_program_version':b.source_program_version,'place_hours':hours,'fictional_only':True}
(P/'final-state.json').write_text(json.dumps(d,indent=2));print(json.dumps({'read_only':True,'checks':len(checks),'failures':0}))
