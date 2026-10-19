import sys
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/m12-full-r1')
from stage_apply import *
S=O/'stages/ingress';assert S.exists()
(S/'IMPLEMENTATION_PLAN.md').write_text('''# Ingress/access/resilience — concrete approved scope

User authorized module12 and related defects. Historical01/02/03/07 reproduced; additional09 API500 on write failure and10 quality-counter500 after successful event share the persistence boundary. Fresh48-method REDr2 required before applying. REDr1 contains one own deleted-fixture reactivation/location ValidationError; own fixture setup corrected without changing any assertion or preexisting test. Both outputs retained.

Modify exactly: domain_admin/site.py (deny before each_context/report with has_view_or_change_permission); views.py (keep full authority/port; map a failed storage signal to503 analytics_unavailable); repositories/tracking_repositories.py (published state guard matching Place.is_public, retain active/deleted); services/tracking.py (one _store_event return boundary, route three existing event writes and subject views through it); services/analytics_quality.py (atomic ancillary counter write); add services/analytics_persistence.py and testcases/test_module12_ingress.py.

persist_analytics(write, **payload) invokes the actual write in transaction.atomic, catches DatabaseError outside savepoint and returns False with a constant safe warning. Other errors propagate. TrackingService._store_event(request,**payload) marks only backend request._analytics_persistence_failed on failed persistence. Public readers ignore False as before; tracking endpoint reports503 instead of a false success or generic invalid event. A failed quality counter never overrides a successfully persisted event. No broad catch around catalog/ACL reads, no model/schema/dependency/permission grants or history cleanup.

Acceptance: exactly-once successful writes; no private events;403 role guards; exact same/trusted ports allowed and other ports/hosts/downgrade denied; public200 with simulated repository failure, real SQL savepoint recovery; API503 and no event; healthy event survives ancillary failure. Existing tracking/AI/V2/owner + Module11 HEAD/public tests unchanged and fresh GREEN. Native rights/contact/public fault/reload follow on actual current source.
''')
files={}
def change(path,old,new,count=1):
 data=files.get(path,(R/path).read_bytes()).decode();assert data.count(old)==count,(path,old,data.count(old));files[path]=data.replace(old,new).encode()
change('src/catalog/domain_admin/site.py','    def changelist_view(self, request, extra_context=None):\n        try:\n            period_days', '    def changelist_view(self, request, extra_context=None):\n        if not self.has_view_or_change_permission(request):\n            raise PermissionDenied\n        try:\n            period_days')
change('src/catalog/views.py','hosts = {request.get_host().split(":", 1)[0].lower()}','hosts = {request.get_host().lower()}')
change('src/catalog/views.py','host = origin.split("://", 1)[1].split("/", 1)[0].split(":", 1)[0].lower()','host = origin.split("://", 1)[1].split("/", 1)[0].lower()')
change('src/catalog/views.py','    record_analytics_ingress(accepted=1 if result.ok else 0, rejected=0 if result.ok else 1)\n    return JsonResponse(result.as_payload(), status=result.status_code)','    record_analytics_ingress(accepted=1 if result.ok else 0, rejected=0 if result.ok else 1)\n    if not result.ok and getattr(request, "_analytics_persistence_failed", False):\n        return JsonResponse({"ok": False, "error": "analytics_unavailable"}, status=503)\n    return JsonResponse(result.as_payload(), status=result.status_code)')
change('src/catalog/repositories/tracking_repositories.py','pk=place_id, is_active=True, deleted_at__isnull=True','pk=place_id, is_active=True, status=Place.STATUS_PUBLISHED, deleted_at__isnull=True')
files['src/catalog/services/analytics_persistence.py']=b'''"""Isolate optional analytics writes from business transactions and responses."""
import logging
from django.db import DatabaseError, transaction

logger = logging.getLogger(__name__)


def persist_analytics(write, **payload) -> bool:
    try:
        with transaction.atomic():
            write(**payload)
    except DatabaseError:
        # Never include query text, identities or provider payloads in this log.
        logger.warning("Optional analytics persistence unavailable")
        return False
    return True
'''
change('src/catalog/services/tracking.py','from catalog.services.reactions import ensure_session_key','from catalog.services.reactions import ensure_session_key\nfrom catalog.services.analytics_persistence import persist_analytics')
change('src/catalog/services/tracking.py','    def track_event(\n','    def _store_event(self, *, request, **payload) -> bool:\n        saved = persist_analytics(self.event_repository.create_event, **payload)\n        if not saved:\n            request._analytics_persistence_failed = True\n        return saved\n\n    def track_event(\n')
change('src/catalog/services/tracking.py','            self.event_repository.create_event(\n','            return self._store_event(\n                request=request,\n')
change('src/catalog/services/tracking.py','            )\n            return True\n\n        session_key = ensure_session_key(request)', '            )\n\n        session_key = ensure_session_key(request)')
change('src/catalog/services/tracking.py','        self.event_repository.create_event(\n','        return self._store_event(\n            request=request,\n',count=2)
change('src/catalog/services/tracking.py','        )\n        return True\n\n    def track_catalog_funnel_events','        )\n\n    def track_catalog_funnel_events')
change('src/catalog/services/tracking.py','        )\n        return True\n\n    def track_cta_click_event','        )\n\n    def track_cta_click_event')
change('src/catalog/services/tracking.py','    _tracking_service.event_repository.create_event(\n','    return _tracking_service._store_event(\n        request=request,\n')
change('src/catalog/services/tracking.py',"        device_class=classify_device(request), referrer_domain='', campaign='')\n    return True", "        device_class=classify_device(request), referrer_domain='', campaign='')")
path='src/catalog/services/analytics_quality.py';data=(R/path).read_text();data=data.replace('from catalog.models import AnalyticsIngressDaily','from catalog.models import AnalyticsIngressDaily\nfrom catalog.services.analytics_persistence import persist_analytics');data=data.replace('    row, _ = AnalyticsIngressDaily.objects.get_or_create', '    return persist_analytics(_write_ingress, accepted=accepted, rejected=rejected, rate_limited=rate_limited)\n\n\ndef _write_ingress(*, accepted, rejected, rate_limited):\n    row, _ = AnalyticsIngressDaily.objects.get_or_create');files[path]=data.encode()
files['src/catalog/testcases/test_module12_ingress.py']=(Q/'test_m12_ingress_candidate.py').read_bytes()
apply('ingress',files,'stages/ingress/evidence/red-r2.json')
