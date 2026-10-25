"""Build the actual public page from an in-memory, never-saved candidate."""
import copy
import re
from datetime import time
from django.urls import reverse
from django.utils import timezone
from catalog.models import Activity, OfferingGroup, PlacePhoto, PricingPlan, PlaceScheduleDay, PlaceScheduleInterval
from catalog.controllers.place_controller import PlaceController
from catalog.services.public_presentation import current_organization
from catalog.services.pricing_plans import build_pricing_summary, public_pricing_plans, legacy_price_values
from catalog.services.public_favorite_count import build_public_favorite_count, PublicFavoriteCount


def _model(model, values, *, fallback_id):
    fields = {field.attname:field for field in model._meta.concrete_fields}
    obj = model(**{name:fields[name].to_python(value) for name,value in values.items() if name in fields})
    if obj.pk is None: obj.pk = fallback_id
    return obj


def _cached_rows(model, values):
    queryset = model.objects.none()
    queryset._result_cache = values
    return queryset


def _prepare_candidate(preview):
    candidate = preview['candidate']
    data = preview['snapshot']
    live = preview['place']
    candidate._editor_preview_new = preview.get('editor_new',False)
    candidate._prefetched_objects_cache = {}
    candidate._public_batch = True
    candidate._public_visible = True
    candidate._public_organization = None if preview.get('editor_new') else current_organization(live)
    # Visibility is simulated only on this unsaved instance. Related drafts
    # keep their real status; only newly submitted tree nodes are published
    # by the existing complete-tree application contract.
    candidate.status = 'published'
    candidate.is_active = True
    if preview['show_submission']:
        for name in ('nature','operating_state'):
            if data.get(name) != getattr(live,name): setattr(candidate,name+'_approved_at',timezone.now())
    photos = [_model(PlacePhoto, row, fallback_id=10**9+i) for i,row in enumerate(data.get('gallery',[]))]
    files = []
    seen = set()
    def add(file):
        if candidate._public_file_exists(file) and file.name not in seen:
            seen.add(file.name);files.append(file)
    add(candidate.photo)
    if not files: add(candidate.cover_photo)
    for photo in sorted(photos,key=lambda photo:(photo.order,photo.pk)): add(photo.image)
    candidate.gallery_files = lambda: files

    days = []
    for row in data.get('structured_schedule',[]):
        day = PlaceScheduleDay(place=candidate,weekday=row['weekday'],is_closed=row.get('is_closed',False),is_24_hours=row.get('is_24_hours',False))
        day.pk = len(days)+1
        intervals = [PlaceScheduleInterval(schedule_day=day,start_time=time.fromisoformat(interval['start']),end_time=time.fromisoformat(interval['end'])) for interval in row.get('intervals',[])]
        day._prefetched_objects_cache = {'intervals':_cached_rows(PlaceScheduleInterval,intervals)}
        days.append(day)
    candidate._prefetched_objects_cache['schedule_days'] = _cached_rows(PlaceScheduleDay,days)

    plans = []
    def tariffs(rows, *, reorder=False, **target):
        result = []
        for index,row in enumerate(rows):
            plan = _model(PricingPlan,row,fallback_id=10**9+len(plans))
            if reorder: plan.sort_order = index
            for name,value in target.items(): setattr(plan,name,value)
            plans.append(plan);result.append(plan)
        return result
    tariffs(data.get('pricing_plans',[]),reorder='pricing_plans' in preview['submitted_fields'],place=candidate,offering_group=None)
    stored = (Activity.objects.none() if preview.get('editor_new') else Activity.objects.filter(place_id=live.pk)).in_bulk()
    activities = []
    for index,row in enumerate((data.get('nested_pricing') or {}).get('activities',[])):
        existing = stored.get(row.get('id'))
        if existing and (existing.status!='published' or existing.archived_at): continue
        activity = copy.copy(existing) if existing else Activity(status='published')
        activity._state = copy.copy(activity._state)
        activity._state.fields_cache = {}
        for name,value in row.items():
            if name=='groups': continue
            field = next((field for field in Activity._meta.concrete_fields if name in (field.name,field.attname)),None)
            if field is not None: setattr(activity,field.attname,field.to_python(value))
        if activity.pk is None: activity.pk=10**9+index
        if existing and existing.program_id!=activity.program_id and activity.program_id:
            activity.program_snapshot={}
        activity.place = candidate
        activity._public_batch = True
        activity._public_visible = True
        activity._public_organization = candidate._public_organization
        activity._public_groups = []
        for group_index,group_row in enumerate(row.get('groups',[])):
            group = _model(OfferingGroup,group_row,fallback_id=10**9+group_index)
            group.activity = activity
            group._public_plans = [plan for plan in tariffs(group_row.get('pricing_plans',[]),reorder='nested_pricing' in preview['submitted_fields'],place=None,offering_group=group) if plan.is_active]
            activity._public_groups.append(group)
        activities.append(activity)
    candidate._pricing_records_cache = sorted(plans,key=lambda plan:(plan.sort_order,plan.pk))
    if {'pricing_plans','nested_pricing'} & preview['submitted_fields']:
        for name,value in legacy_price_values(candidate._pricing_records_cache).items(): setattr(candidate,name,value)
    candidate._site_preview_activities = activities
    if 'editor_images' in preview:
        images = [image for image in preview['editor_images'] if candidate._public_file_exists(image)]
        candidate.gallery_files = lambda: images
        candidate.photo = images[0] if images else ''
    return candidate


def build_site_preview_context(request, preview):
    place = _prepare_candidate(preview)
    request._seo_place = place
    context = PlaceController.build_default().build_detail_context(request,place=place,preview=True)
    contacts = context['presentation']['contacts']
    from catalog.services.public_presentation import revealed_contacts
    contact_payload = revealed_contacts(contacts)
    context.update(
        site_preview=True, site_preview_submission=preview['show_submission'], site_preview_stale=preview['stale'],
        site_preview_phones={'place_id':place.pk, **contact_payload},
        request=request, user=request.user, google_analytics_enabled=False,
        analytics_events=[], queued_analytics_events=[], messages=[],
        public_pricing_plans=public_pricing_plans(place.pricing_plans,request.LANGUAGE_CODE),
        pricing_summary=build_pricing_summary(place,request.LANGUAGE_CODE),
        favorite_social_proof=PublicFavoriteCount(False,None) if preview.get('editor_new') else build_public_favorite_count(place_id=place.pk,site_settings=_preview_site_settings()),
        catalog_return_url=reverse('admin:catalog_placeownershiprequest_changelist'),
    )
    # Share controls show the eventual public address, not a private admin URL.
    build_uri = request.build_absolute_uri
    public_uri = build_uri(place.get_absolute_url())
    request.build_absolute_uri = lambda location=None: build_uri(location) if location is not None else public_uri
    for activity, presentation in zip(place._site_preview_activities,context['activities']):
        if not preview['place'].is_public or activity.pk>=10**9: presentation['url']=''
    return context


def render_site_preview(request, preview, *, language, back_url, return_params=None):
    """Render a guest-looking private page while retaining the real admin session."""
    from django.contrib.auth.models import AnonymousUser
    from django.template.response import TemplateResponse
    from django.utils.translation import override
    from urllib.parse import urlencode

    visitor = copy.copy(request)
    visitor.user = AnonymousUser()
    visitor.LANGUAGE_CODE = language
    visitor.site_preview = True
    with override(language):
        context = build_site_preview_context(visitor, preview)
        context['site_preview_back'] = back_url
        context['catalog_return_url'] = back_url
        context['language_urls'] = {
            lang: request.path + '?' + urlencode({**(return_params or {}), 'lang': lang})
            for lang in ('az', 'ru', 'en')
        }
        context['language_switch_query'] = ''
        context['site_preview_languages'] = context['language_urls'].items()
        context['site_preview_version'] = request.GET.get('version', '')
        if preview.get('editor_current'):
            context['site_preview_editor_current'] = True
            context['site_preview_languages'] = ()
        response = TemplateResponse(visitor, 'catalog/place_detail_preview.html', context)
        response.render()
    response['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
    response['Content-Language'] = language
    return response


def _preview_site_settings():
    from catalog.models import SiteSettings
    return SiteSettings.objects.order_by('pk').first() or SiteSettings()
