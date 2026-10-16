import json
from pathlib import Path
from django.db import transaction,connection
from catalog.models import Place,Activity,PricingPlan,ServerDraft,VolunteerPlaceRevision
P=Path(__file__).resolve().parent;f=json.loads((P/'fixtures.json').read_text())
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 pl=Place.objects.get(pk=f['place']);a=Activity.objects.get(pk=f['activity']);price=PricingPlan.objects.get(pk=f['plan']);rev=VolunteerPlaceRevision.objects.get(place=pl);ds=list(ServerDraft.objects.filter(actor__username='offerqa07_owner',target_id=pl.pk))
 assert a.name_az=='NEW approved OFFER07' and str(price.price)=='35.00' and rev.status=='approved'
 assert any(d.materialized_place_id==pl.pk and 'OLD working copy OFFER07' in json.dumps(d.fields) for d in ds)
 assert any(d.materialized_place_id is None and d.source_version==pl.content_version and 'TYPED after delayed read OFFER07' in json.dumps(d.fields) for d in ds)
 data={'transaction':'READ ONLY','source_version':pl.content_version,'activity':a.name_az,'price':str(price.price),'revision':rev.status,'retained_retired_copies':sum(d.materialized_place_id is not None for d in ds),'active_private_copies':sum(d.materialized_place_id is None for d in ds),'old_input_retained':True,'new_private_typing_saved':True,'live_B_unchanged':True}
(P/'readback.json').write_text(json.dumps(data,indent=2));print('Live B intact; old input retained; explicit/private recovery and delayed typing saved.')
