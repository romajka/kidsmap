"""Explicit opt-in SIMULATED local reporting/failure adapters; no external transport."""
import threading,time
from unittest.mock import patch
from django.db import DatabaseError
from catalog.services.google_analytics_reporting import GoogleAnalyticsAdminSnapshot
LOCK=threading.RLock()
class Adapters:
 def __init__(self,get_response):self.get_response=get_response
 def __call__(self,request):
  mode=request.GET.get('qa_ga','')
  failure=request.headers.get('X-QA-Failure','')
  if mode not in ['filled','error','slow'] and failure not in ['event-store','owner-metrics']:return self.get_response(request)
  assert request.META.get('REMOTE_ADDR') in ['127.0.0.1','::1']
  with LOCK:
   if failure=='event-store':
    with patch('catalog.repositories.tracking_repositories.DjangoFunnelEventRepository.create_event',side_effect=DatabaseError('SIMULATED isolated event store unavailable')):response=self.get_response(request)
   elif failure=='owner-metrics':
    with patch('catalog.controllers.owner_analytics_controller.build_subject_metrics',side_effect=DatabaseError('SIMULATED isolated metrics unavailable')):response=self.get_response(request)
   else:
    snapshot=GoogleAnalyticsAdminSnapshot()
    if mode=='error':snapshot.error='SIMULATED report backend unavailable'
    else:
     snapshot.enabled=True;snapshot.connected=True
     snapshot.period_stats={key:{'active_users':n,'sessions':n+1,'page_views':n+2} for key,n in [('day',10),('week',70),('month',300),('year',3650)]}
     snapshot.daily_chart={'labels':['30.09','01.10'],'active_users':[3,4],'page_views':[5,6]}
     snapshot.top_events=[{'event_name':'phone_click','event_count':12},{'event_name':'whatsapp_click','event_count':8}]
     snapshot.top_pages=[{'page_path':'/ru/places/fictional-'+('very-long-name-'*20)+'/','page_views':25}]
    if mode=='slow':time.sleep(1.2)
    with patch('catalog.services.admin_analytics.build_google_analytics_context',return_value=snapshot.as_context()):response=self.get_response(request)
   response['X-QA-Adapter']='SIMULATED';return response
