import sys,json
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/m11-full-r1')
from stage_apply import *
S=O/'stages/routes';n=json.loads((S/'evidence/red-r2.json').read_text());assert len(n['failures'])==13 and not n['errors'];(S/'IMPLEMENTATION_PLAN.md').write_text('# SEO04/07 and measured related08 plan\n\nUser authorized all module and discovered related defects. Fresh7method RED10observations confirms absent Event sitemap and HEAD405; added rendered specialist landmark regression3language RED after native18nested-main failures. Total8methods13REDobservations. Existing title/default/privacy/editor regression remains passing under social stage.\n\nSEO04: add EventSitemap in src/catalog/sitemaps.py using existing query_public_events(period=EventPeriod(None,None)), retaining exact feature/public interval/status/deleted guards and truthful historical/cancelled/rescheduled public occurrences; lastmod updated_at. Register EventSitemap under events in src/config/urls.py. Inherit existing configured-origin/i18n/alternates/xdefault behavior, no duplicate public predicate or DB change.\n\nSEO07: src/catalog/controllers/public_details.py two @require_GET become @require_safe, retaining existing Organization/Activity approved presentation/visibility/feature guards; unsafe verbs405 and bodyless HEAD checked via actual Django client.\n\nSEO08 related native discovery: specialist_detail.html has inner main while base already main. Replace only inner main start/end with div preserving class/content/IDs; bounded CSS source uses class selectors, no tag dependency found. No CSS/layout/text change. New test_module11_routes.py8methods. Scope4application files+one testfile. Native rerun same social matrix including original failed18semantic cells, HEAD/status and XMLmembership3languages. Full regressions later. No production/schema/permission/source-test assertion edits.\n')
p='src/catalog/sitemaps.py';t=(R/p).read_text();t+='''

class EventSitemap(LocalizedSitemap):
    """All publicly readable occurrences, including retained historical pages."""

    def items(self):
        from catalog.services.event_queries import EventPeriod, query_public_events
        return query_public_events(period=EventPeriod(None, None)).order_by("pk")

    def lastmod(self, obj):
        return obj.updated_at
'''
q='src/config/urls.py';u=(R/q).read_text();old='SpecialistSitemap, OrganizationSitemap, ActivitySitemap';assert u.count(old)==1;u=u.replace(old,old+', EventSitemap');old='    "specialists": SpecialistSitemap,';assert u.count(old)==1;u=u.replace(old,old+'\n    "events": EventSitemap,')
c='src/catalog/controllers/public_details.py';v=(R/c).read_text();assert v.count('@require_GET')==2 and v.count('import require_GET')==1;v=v.replace('import require_GET','import require_safe').replace('@require_GET','@require_safe')
s='src/catalog/templates/catalog/specialist_detail.html';w=(R/s).read_text();old='<main class="km-detail-main-column">';assert w.count(old)==1 and w.count('</main>')==1;w=w.replace(old,'<div class="km-detail-main-column">').replace('</main>','</div>')
apply('routes',{p:t.encode(),q:u.encode(),c:v.encode(),s:w.encode(),'src/catalog/testcases/test_module11_routes.py':(Q/'test_m11_routes_candidate.py').read_bytes()},'stages/routes/evidence/red-r2.json')
