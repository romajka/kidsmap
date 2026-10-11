"""Aggregate/sentinel checks for synthetic browser fixtures, no session or user rows."""
import hashlib
import json
from pathlib import Path
from catalog.models import Place,VolunteerPlaceRevision
HERE=Path(__file__).resolve().parent
rows=[]
for place in Place.objects.order_by('pk'):
    revision=VolunteerPlaceRevision.objects.filter(place=place).first()
    rows.append({'place_id':place.pk,'status':place.status,'is_public':place.is_public,
      'price_from':str(place.price_from),'nature':place.nature,'district':place.district,
      'description_sha256':hashlib.sha256(place.description_az.encode()).hexdigest(),
      'category':place.category_id,'subcategory':place.subcategory_id,
      'revision_status':revision.status if revision else None,
      'revision_fields':revision.changed_fields if revision else [],
      'revision_note_present':bool(revision and revision.review_note),
      'revision_nature':revision.payload.get('nature') if revision else None,
      'revision_district':revision.payload.get('district') if revision else None})
(HERE/'browser-db-readback.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows,ensure_ascii=False))
