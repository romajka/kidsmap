import json
from pathlib import Path
from django.urls import path
from django.http import JsonResponse
from django.conf import settings
from django.db import transaction,connection
from config.urls import urlpatterns as application
def state(request):
 assert settings.TESTING and settings.DATABASES['default']['NAME']=='m09full_r1'
 from catalog.models import Place,SiteReview,PlaceLike,WorkflowNotification,OwnerTeamMembership,OwnerTeamInvitation
 from catalog.services.review_versions import review_types,rating_summary
 with transaction.atomic():
  with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
  x={'typed':{},'summaries':{},'site':list(SiteReview.objects.values('id','user_id','text','rating','status','is_approved','likes_count','dislikes_count')),'favorites':list(PlaceLike.objects.values('id','place_id','user_id')),'places':list(Place.objects.values('id','status','is_active','deleted_at','rating_avg','rating_count','likes_count')),'notifications':list(WorkflowNotification.objects.values('id','event_kind','entity_type','entity_id','entity_version','recipient_user_id','read_at')),'invitations':list(OwnerTeamInvitation.objects.values('id','place_id','status','invited_user_id','email')),'memberships':list(OwnerTeamMembership.objects.values('id','place_id','member_id','is_active'))}
  for kind,(targets,heads,revisions,reactions) in review_types().items():
   x['typed'][kind]={'heads':list(heads.objects.values('id',kind+'_id','user_id','rating','text','status','is_approved','current_revision_id','candidate_revision_id','rejection_reason','likes_count','dislikes_count')),'revisions':list(revisions.objects.values('id','review_id','text','rating','status','rejection_reason')),'reactions':list(reactions.objects.values('id','review_id','revision_id','user_id','value'))}
   response=heads._meta.apps.get_model('catalog',heads.__name__+'Response')
   x['typed'][kind]['responses']=list(response.objects.values('id','revision_id','actor_id','kind','text'))
   x['summaries'][kind]={str(t.pk):rating_summary(t) for t in targets.objects.all()}
 return JsonResponse(x)
def fixture_login(request,role):
 from django.contrib.auth import login,logout,get_user_model
 from django.shortcuts import redirect
 assert role in ['guest','author','owner','employee','outsider','moderator','staff','admin','empty','invitee']
 if role=='guest':logout(request)
 else:login(request,get_user_model().objects.get(username='qa09_'+role),backend='django.contrib.auth.backends.ModelBackend')
 return redirect('site_reviews')
urlpatterns=[path('qa/login/<str:role>/',fixture_login),path('qa/state/',state)]+application
