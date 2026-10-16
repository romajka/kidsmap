"""Additional fictional-only local audit fixtures, executed by isolated runtime."""
from catalog.models import PlaceOwnershipRequest,Place
from django.contrib.auth import get_user_model
f=json.loads((S/'fixtures.json').read_text());u=get_user_model().objects.get(username='fictional_author_0');p=Place.objects.get(pk=f['pending_place'])
request=PlaceOwnershipRequest.objects.create(place=p,applicant=u,note='Fictional stale ownership request')
PlaceOwnershipRequest.objects.filter(pk=request.pk).update(base_ownership_version=p.ownership_version+1)
f.update(ownership_request=request.pk,author_username=u.username,original_candidate_ids={str(x['head']):x['candidate']for x in f['reviews']})
(S/'fixtures.json').write_text(json.dumps(f,indent=2));print('Added one fictional stale request')
