import json
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from catalog.models import PlaceReview,SiteReview
from catalog.testcases.utils import create_ready_place
@transaction.atomic
def seed():
 U=get_user_model();assert not U.objects.exists();author=U.objects.create_user('s09-author',email='author@example.invalid');place=create_ready_place(name='Fictional feed place',name_az='Uydurma məkan',name_ru='Вымышленное место',name_en='Fictional place');records=[]
 for i in range(29):
  u=U.objects.create_user('s09-reviewer-'+str(i),email='reviewer'+str(i)+'@example.invalid');likes=(i*7)%31;dislikes=(i*11)%17;created=timezone.now()-timedelta(days=29-i)
  pr=PlaceReview.objects.create(place=place,user=u,author_name=f'Fictional {i:02}',rating=4,text=f'Fictional place review {i:02}',status='approved',is_approved=True)
  sr=SiteReview.objects.create(user=u,author_name=f'Fictional {i:02}',rating=4,text=f'Fictional site review {i:02}',status='approved',is_approved=True)
  for model,row in [(PlaceReview,pr),(SiteReview,sr)]:model.objects.filter(pk=row.pk).update(likes_count=likes,dislikes_count=dislikes,created_at=created)
  records.append(dict(i=i,place_pk=pr.pk,site_pk=sr.pk,likes=likes,dislikes=dislikes))
 keys={'popular':lambda x:(-(x['likes']-x['dislikes']),-x['likes'],-x['i']),'likes':lambda x:(-x['likes'],x['dislikes'],-x['i']),'dislikes':lambda x:(-x['dislikes'],-x['i']),'date':lambda x:(-x['i'],)}
 expected={sort:{kind:[f'Fictional {kind} review '+format(x['i'],'02') for x in sorted(records,key=key)] for kind in ['place','site']} for sort,key in keys.items()}
 (settings.QA_ROOT/'fixtures.json').write_text(json.dumps({'place_id':place.pk,'expected':expected,'count':29},indent=2));print('29approved fictional place+29site reviews seeded; independent literal sort expectations, no external delivery')
