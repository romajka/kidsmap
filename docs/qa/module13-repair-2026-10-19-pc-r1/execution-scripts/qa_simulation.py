"""Explicitly simulated provider/storage faults on a disposable QA instance only."""
import json
from contextlib import ExitStack
from unittest.mock import patch
from django.test import override_settings
from django.conf import settings
from django.db import DatabaseError
from catalog.services.google_analytics_reporting import GoogleAnalyticsAdminSnapshot

COUNTERS={'provider_stub_calls':0,'storage_fault_calls':0,'read_fault_calls':0}

class SimulationMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        assert settings.TESTING
        if settings.DATABASES['default']['NAME']!='m13full_r1':
            return self.get_response(request)
        if request.path.startswith(('/static/','/media/','/qa/')):
            return self.get_response(request)
        mode=json.loads((settings.QA_ROOT/'simulation.json').read_text())
        with ExitStack() as stack:
            if mode['storage']=='disabled':stack.enter_context(override_settings(LOCAL_ANALYTICS_STORAGE_ENABLED=False))
            if mode['report']!='disabled':
                name=mode['report'];stats={key:{'active_users':n,'sessions':n+1,'page_views':n+2} for key,n in [('day',1),('week',7),('month',30),('quarter',90),('year',365)]}
                if name=='empty':stats={k:{x:0 for x in v} for k,v in stats.items()}
                snap=GoogleAnalyticsAdminSnapshot(enabled=True,connected=name in ['filled','empty'],measurement_id='G-FICTIONAL-M13',property_id='123456',error='FICTIONAL_PROVIDER_SECRET_MARKER' if name in ['error','partial'] else '',period_stats=stats,daily_chart={'labels':['17.10','18.10'],'active_users':[7,9],'page_views':[10,15]} if name in ['filled','partial'] else {'labels':[],'active_users':[],'page_views':[]},top_pages=[{'page_path':'/fictional-public/'+('long-'*35),'page_views':15}] if name in ['filled','partial'] else [],top_events=[{'event_name':'phone_click','event_count':2}] if name in ['filled','partial'] else [])
                stub=stack.enter_context(patch('catalog.services.google_analytics_reporting.GoogleAnalyticsAdminReportingService.build_snapshot',return_value=snap))
            else:stub=None
            read_fault=stack.enter_context(patch('catalog.services.analytics_metrics._period_values',side_effect=DatabaseError('fictional aggregate read failure'))) if mode['storage']=='read_failure' else None
            fault=stack.enter_context(patch('catalog.repositories.tracking_repositories.DjangoFunnelEventRepository.create_event',side_effect=DatabaseError('fictional analytics fault'))) if mode['storage']=='failure' else None
            try:return self.get_response(request)
            finally:
                if stub:COUNTERS['provider_stub_calls']+=stub.call_count
                if fault:COUNTERS['storage_fault_calls']+=fault.call_count
                if read_fault:COUNTERS['read_fault_calls']+=read_fault.call_count
