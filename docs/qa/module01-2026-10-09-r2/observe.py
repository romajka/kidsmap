import sys,json
sys.argv=['run.py','observe']
from run import *
from catalog.models import Place,VolunteerPlaceRevision
from catalog.services.publication import snapshot
for place in Place.objects.all():
    revision=VolunteerPlaceRevision.objects.filter(place=place).first()
    current=snapshot(place,'place')
    print(json.dumps({'id':place.pk,'live_photo':bool(place.photo),'live_gallery':place.gallery.count(),'candidate_photo':bool(revision and revision.payload.get('photo')),'candidate_gallery_count':len(revision.payload.get('gallery',[])) if revision else 0,'review_note_present':bool(revision and revision.review_note),'candidate_base_mismatch_keys':[k for k in revision.changed_fields if current.get(k)!=revision.base_snapshot.get(k)] if revision else []},ensure_ascii=True))
