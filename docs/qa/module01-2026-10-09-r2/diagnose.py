import sys,json
sys.argv=['run.py','diagnostic']
from run import *
from django.test import Client
from django.test.utils import setup_test_environment
from django.contrib.auth import get_user_model
from django.core import signing
from catalog.models import Place,VolunteerPlaceRevision
from catalog.services import publication
setup_test_environment()
c=Client();c.force_login(get_user_model().objects.get(username='qa_owner'))
out=[]
for pk in (1,2):
    r=c.get(f'/ru/account/places/{pk}/edit/')
    form=r.context['form'];token=form.initial['publication_token'];d=signing.loads(token,salt='publication-source');live=Place.objects.get(pk=pk);snap=publication.snapshot(live,'place')
    out.append({'id':pk,'http':r.status_code,'token_source_matches':d['source']==live.content_version,'snapshot_mismatch_keys':[k for k in snap if snap[k]!=d['snapshot'].get(k)],'dependencies_match':d['dependencies']==publication.dependencies(live,'place'),'gallery_preview_count':len(form.saved_gallery_preview)})
(HERE/'diagnostic.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out))

rows=[]
for place in Place.objects.all():
 rev=VolunteerPlaceRevision.objects.filter(place=place).first()
 snap=publication.snapshot(place,'place')
 rows.append({'id':place.pk,'status':place.status,'revision_status':rev.status if rev else None,'changed_fields':rev.changed_fields if rev else [],'base_mismatch_keys':[k for k in rev.changed_fields if snap.get(k)!=rev.base_snapshot.get(k)] if rev else [],'live_price_from':str(place.price_from),'live_price_to':str(place.price_to),'candidate_prices':{k:rev.payload.get(k) for k in ['price_from','price_to']} if rev else {},'review_note_present':bool(rev and rev.review_note)})
(HERE/'candidate-diagnostic.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows))
