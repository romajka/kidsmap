"""Owned local-only fixture/readback routes, never part of application URLconf."""
import json,os
from django.conf import settings
from django.http import JsonResponse
from django.urls import path
from django.db import transaction,connection
from config.urls import urlpatterns as application

def local(request):
 return settings.TESTING and request.META.get('REMOTE_ADDR')=='127.0.0.1'

def fixtures(request):
 assert local(request)
 data=json.loads((settings.QA_ROOT/'fixtures.json').read_text())
 data['password']=json.loads((settings.QA_ROOT/'secrets.json').read_text())['login_password']
 return JsonResponse(data)

def state(request):
 assert local(request) and request.user.is_authenticated and request.user.is_superuser
 from catalog.models import Place,PlaceReview,PlaceOwnershipRequest
 from catalog.services.content_quality import approved_review_queryset,public_place_queryset
 result={'pid':os.getpid(),'read_only':True,'synthetic_only':True,'reviews':[]}
 with transaction.atomic():
  with connection.cursor()as cur:
   cur.execute('SET TRANSACTION READ ONLY');cur.execute("SET LOCAL statement_timeout='5s'");cur.execute("SET LOCAL lock_timeout='2s'")
  for h in PlaceReview.objects.order_by('pk'):
   result['reviews'].append({'id':h.pk,'user':h.user_id,'status':h.status,'approved':h.is_approved,'current':h.current_revision_id,'candidate':h.candidate_revision_id,'text':h.text,'rating':h.rating,'public':approved_review_queryset(PlaceReview.objects.filter(pk=h.pk)).exists(),'revisions':list(h.revisions.order_by('pk').values('id','status','rating','text'))})
  result['places']=list(Place.objects.order_by('pk').values('id','status','is_active','rating_avg','rating_count'))
  result['public_places']=list(public_place_queryset(Place.objects.all()).values_list('pk',flat=True))
  result['requests']=list(PlaceOwnershipRequest.objects.values('id','status','base_ownership_version'))
 return JsonResponse(result)

urlpatterns=[path('admin/qa/fixtures/',fixtures),path('admin/qa/state/',state)]+application
