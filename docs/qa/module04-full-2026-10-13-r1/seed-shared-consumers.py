import json
from pathlib import Path
from catalog.models import PlaceReview,PlaceOwnershipRequest
P=Path(__file__).resolve().parent;g=json.loads((P/'fixtures.json').read_text())
r=PlaceReview.objects.create(place_id=g['venues']['public'],user_id=g['actors']['empty'],text='Synthetic QA shared consumer review',author_name='Synthetic fixture')
c=PlaceOwnershipRequest.objects.create(place_id=g['venues']['public'],applicant_id=g['actors']['empty'])
(P/'shared-fixtures.json').write_text(json.dumps({'review':r.pk,'claim':c.pk}));print(json.dumps({'fictional_shared_consumer_fixtures':2,'event_writes':0}))
