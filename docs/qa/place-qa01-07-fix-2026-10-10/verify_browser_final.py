import json
from pathlib import Path
from catalog.models import Place,VolunteerPlaceRevision
HERE=Path(__file__).resolve().parent
one=Place.objects.get(pk=1);r1=VolunteerPlaceRevision.objects.get(place=one)
two=Place.objects.get(pk=2);r2=VolunteerPlaceRevision.objects.get(place=two)
three=Place.objects.get(pk=3);r3=VolunteerPlaceRevision.objects.get(place=three)
sentinel='KMFIX description saved from translated admin. Synthetic content for a controlled local test; other fields must retain their stored values.'
assert r1.payload['description_az']==sentinel and r1.payload['category']=='KMFIX_NEXT' and r1.payload['subcategory']==106
assert two.name_az=='KMFIX Competitor approved live' and r2.status=='approved'
assert str(two.price_from)==str(two.pricing_plan_records.get().price)=='27.00'
assert two.pricing_plan_records.get().pk==1
assert r3.payload['nature']=='public_space' and three.nature is None and three.nature_approved_at is None
result={'admin_description_stored_in_revision':True,'admin_taxonomy_stored_in_revision':True,
 'stale_tab_input_did_not_overwrite_revision':True,'stale_review_did_not_overwrite_competitor':True,
 'plan_identity_stable':True,'last_canonical_and_projected_price':'27.00',
 'nature_machine_value_stored':True,'live_nature_and_approval_facts_unchanged':True}
(HERE/'browser-final-db.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
