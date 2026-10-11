"""Stored canonical amount and mixed candidate diagnostics."""
import json
import sys
from pathlib import Path
from catalog.models import Place,VolunteerPlaceRevision
from catalog.services.volunteer_places import revision_base_matches
HERE=Path(__file__).resolve().parent
phase=sys.argv[3];place=Place.objects.get(pk=2);revision=VolunteerPlaceRevision.objects.get(place=place)
plan=place.pricing_plan_records.get()
expected_name='KMFIX Yeni təsdiqlənəcək məkan';expected_address='KMFIX New mixed address 18'
row={'phase':phase,'plan_id':plan.pk,'canonical_amount':str(plan.price),'projected_amount':str(place.price_from),
     'revision_status':revision.status,'changed_fields':revision.changed_fields,'base_matches':revision_base_matches(revision,place),
     'live_identity_matches':place.name_az==expected_name and place.address==expected_address,
     'is_public':place.is_public,'self_price_fields_in_candidate':sorted(set(revision.changed_fields)&{'price_from','price_to','price_per_lesson','price_per_month','price_per_8_lessons'})}
assert row['canonical_amount']==row['projected_amount']=='18.00'
assert row['live_identity_matches']==(phase=='approved')
if phase!='approved':assert row['base_matches'] and not row['self_price_fields_in_candidate']
(HERE/f'pricing-db-{phase}.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8')
print(json.dumps(row))
