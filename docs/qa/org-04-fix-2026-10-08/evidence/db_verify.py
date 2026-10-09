from pathlib import Path
import json,hashlib
from django.apps import apps
from catalog.models import Place,Activity,PlacePhoto,PricingPlan,OfferingGroup,PlaceScheduleInterval,OrganizationConnectionOperation
from catalog.services import organization_connections as connections,business_team
from django.contrib.auth import get_user_model
s=Path(__file__).parent;b=json.loads((s/'db-before.json').read_text());changed=[];new={}
for name,before in b.items():
 model=apps.get_model('catalog',name)
 after={str(r['id']):hashlib.sha256(json.dumps(r,sort_keys=True,default=str).encode()).hexdigest() for r in model.objects.values()}
 changed += [name+':'+pk for pk,h in before.items() if after.get(pk)!=h]
 new[name]=len(after.keys()-before.keys())
assert not changed,changed
f=json.loads((s/'fixtures.json').read_text());ids=[r['id'] for r in f['places']]+[f['private_place']]
assert Place.objects.filter(pk__in=ids,organization__isnull=True).count()==9
first=Place.objects.get(pk=ids[0]);activity=Activity.objects.get(place=first)
assert activity.program_id is None and activity.source_program_id and activity.source_program_version
assert activity.program_snapshot['description_az']=='Synthetic approved description'
assert activity.supplement_az=='Synthetic local text'
assert list(PlacePhoto.objects.filter(place=first).values_list('order',flat=True))==[2,7]
assert OfferingGroup.objects.get(activity=activity).schedule_text=='Saturday 14:00'
assert PricingPlan.objects.get(place=first).price==77
assert PlaceScheduleInterval.objects.get(schedule_day__place=first).start_time.hour==9
owner=get_user_model().objects.get(username='demo_owner')
private=Place.objects.get(pk=f['private_place']);assert not connections.visible_places(owner).filter(pk=private.pk).exists()
results={'old_domain_rows_unchanged':sum(map(len,b.values())),'changed_old_rows':changed,'new_synthetic_rows':new,'synthetic_places_detached':9,'gallery_order_retained':True,'program_local_snapshot_retained':True,'group_price_hours_retained':True,'private_display_still_denied':True}
(s/'db-after.json').write_text(json.dumps(results,indent=2));print(results)
