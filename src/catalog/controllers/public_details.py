"""Public approved Organization and concrete Place Activity pages."""
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from catalog.models import Organization, Activity, PlaceReview, ActivityReview
from catalog.services.content_quality import published_place_queryset, public_review_queryset
from catalog.services.public_presentation import present, current_organization, translated
from catalog.services.tracking import track_subject_view
from catalog.services.seo import build_public_entity_seo_payload


def _language(request):
    return getattr(request, 'LANGUAGE_CODE', 'az')


@require_GET
def organization_detail(request, public_id):
    from catalog.services.features import require_organizations_section_enabled
    require_organizations_section_enabled()
    entity = get_object_or_404(Organization, public_id=public_id)
    lang = _language(request)
    data = present(entity, lang)
    if not data['visible']:
        raise Http404
    request._seo_entity = entity
    branch_objects = [p for p in published_place_queryset(entity.places.all()).select_related('category','organization')
        if current_organization(p) is not None]
    branches = []
    districts_map = {}
    activities_map = {}
    for place in branch_objects:
        branch = present(place, lang)
        branch_activities = [present(activity, lang) for activity in place.activities.filter(
            status='published', archived_at__isnull=True).select_related('place__organization', 'place__category', 'program__organization')]
        
        district_key = place.district or ''
        district_label = place.district_i18n(lang) if district_key else ''
        if district_key:
            if district_key not in districts_map:
                districts_map[district_key] = {'key': district_key, 'label': district_label, 'count': 0}
            districts_map[district_key]['count'] += 1

        act_names = []
        for a in branch_activities:
            name = a.get('name')
            if name:
                act_names.append(name)
                activities_map[name] = activities_map.get(name, 0) + 1

        branch.update(
            age=place.age_display,
            address=translated(place, 'address', lang)[0],
            district=district_key,
            district_label=district_label,
            activities=branch_activities,
            activities_list=act_names
        )
        branches.append(branch)

    districts_filter = sorted(districts_map.values(), key=lambda d: d['label'])
    activities_filter = sorted([{'name': k, 'count': v} for k, v in activities_map.items()], key=lambda a: a['name'])
    programs = [present(p, lang) for p in entity.programs.filter(status='published', approved_at__isnull=False, archived_at__isnull=True)]
    feed = []
    for review in public_review_queryset(PlaceReview.objects.filter(place_id__in=[p.pk for p in branch_objects])).select_related('place').order_by('-created_at')[:30]:
        target = present(review.place, lang)
        feed.append({'target_name':target['name'], 'target_url':target['url']+'#reviews', 'text':review.text, 'rating':review.rating})
    for review in public_review_queryset(ActivityReview.objects.filter(activity__place_id__in=[p.pk for p in branch_objects],
            activity__status='published', activity__archived_at__isnull=True)).select_related('activity__place__category', 'activity__program__organization').order_by('-created_at')[:30]:
        target = present(review.activity, lang)
        if target['visible']:
            feed.append({'target_name':target['name'], 'target_url':target['url']+'#reviews', 'text':review.text, 'rating':review.rating})
    # Top directions summary for compact hero block
    top_directions = [a['name'] for a in activities_filter[:4] if a.get('name')]
    # Suitable photo: entity photo or first published branch photo
    hero_image_url = data.get('image_url') or next((b['image_url'] for b in branches if b.get('image_url')), '')

    from catalog.services.features import is_specialists_section_enabled, is_events_section_enabled
    from django.utils import timezone

    org_specialists = []
    specialists_enabled = is_specialists_section_enabled()
    if specialists_enabled:
        from catalog.models.specialist_domain import SpecialistEmployment
        active_employments = (
            entity.specialist_employments.filter(
                status=SpecialistEmployment.ACTIVE,
                person_confirmed_at__isnull=False,
                organization_confirmed_at__isnull=False,
                specialist__status='published',
                specialist__is_active=True,
            )
            .select_related('specialist', 'specialist__verified_person_user')
            .prefetch_related('specialist__specializations', 'specialist__practice_locations__place')
            .order_by('specialist__name')
        )
        today = timezone.localdate()
        for emp in active_employments:
            if emp.end_date and emp.end_date < today:
                continue
            spec = emp.specialist
            live_consent = bool(
                spec.verified_person_user_id and spec.person_verified_at
                and spec.verified_person_user.is_active
                and entity.owner_id and entity.owner.is_active
                and emp.person_user_id == spec.verified_person_user_id
                and emp.person_confirmed_by_id == spec.verified_person_user_id
                and emp.organization_owner_id == entity.owner_id
                and emp.organization_confirmed_by_id == entity.owner_id
                and emp.organization_ownership_version == entity.ownership_version
            )
            if not live_consent:
                continue
            specs_labels = [s.name_i18n(lang) for s in spec.specializations.all()[:2]]
            spec_branches = [
                loc.place.name_i18n(lang) for loc in spec.practice_locations.filter(is_active=True, place__in=branch_objects)
            ]
            org_specialists.append({
                'specialist': spec,
                'name': spec.name,
                'role': emp.role,
                'url': spec.get_absolute_url(),
                'photo': spec.photo.url if spec.photo else None,
                'specializations': specs_labels,
                'branches': spec_branches,
            })

    org_events = []
    events_enabled = is_events_section_enabled()
    if events_enabled:
        from catalog.services.public_presentation import visible
        events_qs = (
            entity.organized_events.filter(
                status='published',
                deleted_at__isnull=True,
                occurrence_state='scheduled',
                end_datetime__gte=timezone.now(),
            )
            .select_related('related_place')
            .order_by('start_datetime')[:6]
        )
        for ev in events_qs:
            venue_name = ''
            if ev.related_place and visible(ev.related_place):
                venue_name = ev.related_place.name_i18n(lang)
            elif ev.venue_label:
                venue_name = ev.venue_label
            org_events.append({
                'event': ev,
                'name': ev.name_i18n(lang),
                'url': ev.get_absolute_url(),
                'start_datetime': ev.start_datetime,
                'end_datetime': ev.end_datetime,
                'price': ev.price_display,
                'age': ev.age_display,
                'venue_name': venue_name,
                'photo': ev.photo.url if ev.photo else None,
            })

    track_subject_view(request=request, subject=entity)
    return render(request,'catalog/public_entity_detail.html',{
        'entity':entity,
        'presentation':data,
        'branches':branches,
        'branches_count':len(branches),
        'districts_filter':districts_filter,
        'activities_filter':activities_filter,
        'top_directions':top_directions,
        'hero_image_url':hero_image_url,
        'org_specialists':org_specialists,
        'org_events':org_events,
        'specialists_section_enabled':specialists_enabled,
        'events_section_enabled':events_enabled,
        'programs':programs,
        'review_feed':feed,
        **build_public_entity_seo_payload(entity, request, lang)})


@require_GET
def activity_detail(request, pk):
    entity = get_object_or_404(Activity.objects.select_related('place__category','place__organization','program__organization'), pk=pk)
    data = present(entity, _language(request))
    if not data['visible']:
        raise Http404
    request._seo_entity = entity
    feed = [{'target_name':data['name'], 'target_url':data['url']+'#reviews', 'text':review.text, 'rating':review.rating}
        for review in public_review_queryset(ActivityReview.objects.filter(activity=entity)).order_by('-created_at')[:30]]
    track_subject_view(request=request, subject=entity)
    return render(request,'catalog/public_entity_detail.html',{
        'entity':entity,'presentation':data,'place':entity.place,'place_presentation':present(entity.place,_language(request)),
        'review_feed':feed, **build_public_entity_seo_payload(entity, request, _language(request))})
