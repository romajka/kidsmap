import json
from pathlib import Path
from django.db import transaction,connection
from catalog.models import Place,Activity,PricingPlan,ServerDraft,VolunteerPlaceRevision
P=Path('/home/ramin/kidsmap/docs/qa/offer-qa07-recheck-2026-10-14-r1');f=json.loads((P/'fixtures.json').read_text())
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 place=Place.objects.get(pk=f['place']);activity=Activity.objects.get(pk=f['activity']);plan=PricingPlan.objects.get(pk=f['plan']);old=ServerDraft.objects.get(pk=f['old_draft_id']);rev=VolunteerPlaceRevision.objects.get(place=place)
 data={'transaction':'READ ONLY','place_content_version':place.content_version,'live_activity':activity.name_az,'live_price':str(plan.price),'revision_status':rev.status,'old_draft':{'source_version':old.source_version,'version':old.version,'materialized_place_id':old.materialized_place_id},'same_actor_target_copies':[{'source_version':x.source_version,'version':x.version,'materialized_place_id':x.materialized_place_id} for x in ServerDraft.objects.filter(actor=old.actor,target_type='place',target_id=place.pk)]}
 assert activity.name_az=='NEW approved OFFER07' and str(plan.price)=='35.00' and rev.status=='approved' and old.source_version<place.content_version and old.materialized_place_id is None,data
(P/'readback.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));print('READ ONLY: B approved/live; A stale and still resumable confirmed.')
