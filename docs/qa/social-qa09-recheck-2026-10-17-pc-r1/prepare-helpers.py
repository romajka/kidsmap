from pathlib import Path
Q=Path(__file__).resolve().parent
(Q/'fixtures.py').write_text('''import json
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
''')
(Q/'qa_urls.py').write_text('''import hashlib,json,platform
from django.conf import settings
from django.contrib.auth import get_user_model,login,logout
from django.db import transaction,connection
from django.http import JsonResponse
from django.shortcuts import redirect
from django.template.loader import get_template
from django.urls import path
from catalog.models import PlaceReview,SiteReview,ReviewReaction

def fixture_login(request,role):
 assert role in ('guest','author')
 if role=='guest':logout(request)
 else:login(request,get_user_model().objects.get(username='s09-author'),backend='django.contrib.auth.backends.ModelBackend')
 return redirect('place_reviews')
def info(request):
 import django
 with connection.cursor() as c:c.execute('SHOW server_version');pg=c.fetchone()[0]
 paths=['src/catalog/services/public_urls.py','src/catalog/middleware.py','src/catalog/controllers/place_reviews_controller.py','src/catalog/context_processors.py','src/catalog/templates/pages/place_reviews.html']
 return JsonResponse(dict(testing=settings.TESTING,python=platform.python_version(),django=django.get_version(),postgresql=pg,source_files=1023,template=get_template('pages/place_reviews.html').origin.name,hashes={p:hashlib.sha256((settings.BASE_DIR/p).read_bytes()).hexdigest() for p in paths},sole_locales=list(map(str,settings.LOCALE_PATHS))))
def state(request):
 with transaction.atomic():
  with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
  return JsonResponse(dict(place_reviews=PlaceReview.objects.count(),site_reviews=SiteReview.objects.count(),place_votes=sum(PlaceReview.objects.values_list('likes_count',flat=True)),site_votes=sum(SiteReview.objects.values_list('likes_count',flat=True))))
from config.urls import urlpatterns as app_urls
urlpatterns=[path('qa/login/<str:role>/',fixture_login),path('qa/info/',info),path('qa/state/',state)]+app_urls
'''.replace(',ReviewReaction',''))
(Q/'browser-initial.js').write_text('''async(page)=>{await page.context().route('**/*',r=>{const u=new URL(r.request().url());return u.hostname==='127.0.0.1'&&u.port==='33369'?r.continue():r.abort('blockedbyclient');});await page.goto('http://127.0.0.1:33369/qa/info/');return {browser:page.context().browser().version(),info:await page.locator('body').innerText()};}''')
print('Fresh09 fixtures/state/info/native browser profile prepared')
